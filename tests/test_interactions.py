from pathlib import Path
import time
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest
from src.data_loader import mocks
from src.data_validation import validate

ROOT=Path(__file__).resolve().parents[1]


def page(name):
    at=AppTest.from_file(ROOT/'pages'/name,default_timeout=40)
    for key,value in dict(authenticated=True,username='admin',role='ADMIN',login_time=time.time()).items():at.session_state[key]=value
    return at.run()


def section(at,label):
    return at.get('button_group')[0].set_value(label).run()


def test_summary_drilldown_and_filters():
    at=page('02_Indicadores.py')
    assert not at.error and not at.exception
    assert not any(s.label=='Indicador de qualidade / monitoramento' for s in at.selectbox)
    next(s for s in at.selectbox if s.label=='Competência do resumo').select('2026-01').run()
    next(s for s in at.selectbox if s.label=='Abrir indicador do resumo').set_value('Q03')
    next(b for b in at.button if b.label=='Ver análise do indicador').click().run()
    assert at.session_state['indicators_section']=='Produção assistencial'
    assert next(s for s in at.selectbox if s.label=='Indicador assistencial').value=='Q03'
    assert next(s for s in at.selectbox if s.label=='Competência').value=='2026-01'
    next(s for s in at.selectbox if s.label=='Ano').select('2024').run()
    assert all(value.startswith('2024') for value in next(s for s in at.selectbox if s.label=='Competência').options)
    next(s for s in at.selectbox if s.label=='Contrato').select('006/2010').run()
    assert not at.exception and not at.error


@pytest.mark.parametrize('name,labels',[
    ('02_Indicadores.py',['Qualidade e monitoramento','Metas e projeções','Gestão de dados','Resumo gerencial']),
    ('03_Instrumentos_de_Gestao.py',['Metas por instrumento','Auditoria e condições financeiras','Biblioteca e linha do tempo']),
    ('04_Pareceres_CMA.py',['Comparação anual','Qualidade e evidências','Pareceres']),
    ('05_Producao_Hospitalar.py',['Perfil assistencial','Valores e permanência','Óbitos e mortalidade','Fontes e tabelas','Visão geral']),
])
def test_sections_render_only_when_selected(name,labels):
    at=page(name)
    for label in labels:
        section(at,label)
        assert not at.exception and not at.error
        assert not at.get('json')


def test_exports_generated_only_on_request(monkeypatch):
    import src.presentation as presentation
    calls=[]
    original=presentation.documentary_workbook
    def spy(*args):calls.append(True);return original(*args)
    monkeypatch.setattr(presentation,'documentary_workbook',spy)
    at=page('02_Indicadores.py')
    assert not calls
    next(c for c in at.checkbox if c.label=='Preparar arquivos para download').check().run()
    assert len(calls)==1
    assert any(d.label=='Baixar relatório XLSX' for d in at.get('download_button'))


def test_cma_pdf_page_and_year_changes():
    at=page('04_Pareceres_CMA.py')
    control=next(n for n in at.number_input if n.label=='Página do parecer')
    if control.max>1:
        control.set_value(2).run()
        assert any('Página 2 de' in c.value for c in at.caption)
        assert at.get('image')
    next(s for s in at.selectbox if s.label=='Ano do parecer').select('2024').run()
    assert next(n for n in at.number_input if n.label=='Página do parecer').value==1
    assert not at.exception and not at.error


@pytest.mark.parametrize('invalid',[False,True])
def test_import_preview_confirmation_and_consolidation(monkeypatch,invalid):
    import streamlit as st
    production,_=mocks()
    production=validate(production,'producao')[0].iloc[:1].copy()
    production['saidas_hospitalares']=-1 if invalid else 900
    class Upload:
        name='agregado.csv'
        def getvalue(self):return production.to_csv(index=False).encode('utf8')
    monkeypatch.setattr(st,'file_uploader',lambda *args,**kwargs:Upload())
    at=AppTest.from_string('from src.data_ui import render_data\nrender_data()',default_timeout=40)
    at.session_state['role']='ADMIN';at.session_state['username']='admin';at.run()
    assert not at.exception
    assert len(at.dataframe)>0  # Mapping and validated preview were rendered.
    if invalid:
        assert any('Arquivo inválido' in error.value for error in at.error)
        assert not any(b.label=='Confirmar consolidação' for b in at.button)
    else:
        button=next(b for b in at.button if b.label=='Confirmar consolidação')
        assert button.disabled
        next(c for c in at.checkbox if c.label.startswith('Confirmo o conjunto')).check().run()
        next(b for b in at.button if b.label=='Confirmar consolidação').click().run()
        merged=at.session_state['production']
        assert merged[merged.competencia==production.iloc[0].competencia].iloc[0].saidas_hospitalares==900
        assert len(at.session_state['import_audit'])==1
        assert not at.exception and not at.error
