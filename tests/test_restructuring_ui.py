"""Real Streamlit widgets, protected navigation and isolated demonstrations."""
import time
from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest
ROOT=Path(__file__).resolve().parents[1]
PAGE=ROOT/'pages/06_Indicadores_de_Reestruturacao.py'


def app(role='ADMIN'):
    at=AppTest.from_file(PAGE,default_timeout=40)
    for key,value in dict(authenticated=True,username='admin' if role=='ADMIN' else 'diretoria',role=role,login_time=time.time()).items():at.session_state[key]=value
    return at.run()


def section(at,label):
    next(group for group in at.get('button_group') if label in group.options).set_value(label).run()
    assert not at.exception and not at.error


def test_protected_and_read_only(monkeypatch):
    monkeypatch.delenv('ADMIN_PASSWORD_HASH',raising=False)
    at=AppTest.from_file(PAGE).run()
    assert not at.exception
    assert not at.dataframe
    at=app('GESTOR')
    assert 'Administração' not in at.get('button_group')[0].options
    next(r for r in at.radio if r.label=='Modo de acompanhamento').set_value('Demonstração fictícia').run()
    assert not at.exception and not at.error
    assert not any('Registrar' in b.label for b in at.button)


def test_demo_all_indicator_charts_and_export():
    at=app()
    next(r for r in at.radio if r.label=='Modo de acompanhamento').set_value('Demonstração fictícia').run()
    section(at,'Acompanhamento e fichas')
    for number in range(1,15):
        at.selectbox(key='restructure_indicator').select(number).run()
        assert not at.exception and not at.error
        assert any('Memória de cálculo' in e.label for e in at.expander)
    next(c for c in at.checkbox if c.label=='Preparar exportação da reestruturação').check().run()
    assert not at.exception and not at.error
    assert len(at.get('download_button'))==2
    section(at,'Administração')
    for label in ['Registros operacionais','Apurações','Pactuação e ficha','Ações para desvios']:
        section(at,label)


def test_persistent_initialization_new_session_and_aggregate(tmp_path,monkeypatch):
    monkeypatch.setenv('RESTRUCTURING_STORAGE_PATH',str(tmp_path/'institutional.json'))
    at=app()
    next(b for b in at.button if b.label=='Inicializar fichas propostas').click().run()
    assert not at.exception and not at.error
    section(at,'Administração');section(at,'Apurações')
    next(s for s in at.selectbox if s.label=='Tipo de apuração').select('Agregada')
    for label,value in [('Numerador (somente na entrada agregada)',8),('Denominador (somente na entrada agregada)',10)]:next(w for w in at.number_input if w.label==label).set_value(value)
    for label in ['Fonte desta apuração','Método desta apuração','Responsável pela coleta da apuração','Responsável pela validação da apuração','Referência da evidência da validação']:next(w for w in at.text_input if w.label==label).set_value('Registro de avaliação agregada')
    for label in ['Universo elegível confirmado (inclusive quando comprovadamente vazio)','Critérios de elegibilidade conferidos']:next(w for w in at.checkbox if w.label==label).check()
    next(b for b in at.button if b.label=='Calcular e registrar apuração').click().run()
    assert not at.exception and not at.error
    reader=app('GESTOR')
    section(reader,'Acompanhamento e fichas')
    assert any(m.value=='80.00%' for m in reader.metric)
    assert 'Administração' not in reader.get('button_group')[0].options


def test_backup_restoration_through_interface(tmp_path,monkeypatch):
    import streamlit as st
    from src.restructuring.repository import Repository,FileStore
    from src.restructuring.schema import Actor
    source=Repository(FileStore(tmp_path/'source.json'))
    actor=Actor('admin','ADMIN',True,time.time());source.initialize(actor)
    content=source.backup(actor)
    class Upload:
        def getvalue(self):return content
    monkeypatch.setenv('RESTRUCTURING_STORAGE_PATH',str(tmp_path/'recovered.json'))
    monkeypatch.setattr(st,'file_uploader',lambda *args,**kwargs:Upload())
    at=app()
    next(w for w in at.text_input if w.label=='Justificativa da restauração').set_value('Recuperação manual de backup confiável')
    next(w for w in at.checkbox if w.label=='Conferi a origem e a confiabilidade do backup').check().run()
    next(b for b in at.button if b.label=='Restaurar backup').click().run()
    assert not at.exception and not at.error
    assert any('14 versões recuperadas' in s.value for s in at.success)
    reader=app('GESTOR')
    assert not reader.exception and not reader.error
    assert any(m.label=='Indicadores propostos' and m.value=='14' for m in reader.metric)
    assert not any(b.label=='Restaurar backup' for b in reader.button)
