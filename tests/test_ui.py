from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
import time
import pytest
from streamlit.testing.v1 import AppTest
@pytest.mark.parametrize('page',['01_Tela_Inicial','02_Indicadores','03_Instrumentos_de_Gestao','04_Pareceres_CMA','05_Producao_Hospitalar'])
def test_pages(page):
    at=AppTest.from_file(ROOT/'pages'/(page+'.py'),default_timeout=40)
    for key,value in dict(authenticated=True,username='admin',role='ADMIN',login_time=time.time()).items():at.session_state[key]=value
    at.run();assert not at.exception
    assert not at.error
    assert not at.get("json")

@pytest.mark.parametrize('page',['01_Tela_Inicial','02_Indicadores','03_Instrumentos_de_Gestao','04_Pareceres_CMA','05_Producao_Hospitalar'])
def test_pages_protected_without_session(page,monkeypatch):
    monkeypatch.delenv('ADMIN_USERNAME',raising=False);monkeypatch.delenv('ADMIN_PASSWORD_HASH',raising=False)
    at=AppTest.from_file(ROOT/'pages'/(page+'.py')).run()
    assert not at.exception
    assert any('Configuração incompleta' in e.value for e in at.error)
    assert not at.dataframe

def test_procedure_groups_all_selected():
    at=AppTest.from_file(ROOT/'pages/05_Producao_Hospitalar.py',default_timeout=40)
    for key,value in dict(authenticated=True,username='admin',role='ADMIN',login_time=time.time()).items():at.session_state[key]=value
    at.run()
    at.get('button_group')[0].set_value('Perfil assistencial').run()
    next(s for s in at.selectbox if s.label=='Classificação da produção').select('Grupo procedimento').run()
    selection=next(s for s in at.multiselect if s.label=='Categorias para comparar')
    assert set(selection.value)==set(selection.options)
    assert not at.error and not at.exception

def test_director_has_no_data_management_tab():
    at=AppTest.from_file(ROOT/'pages/02_Indicadores.py',default_timeout=40)
    for key,value in dict(authenticated=True,username='diretoria',role='GESTOR',login_time=time.time()).items():at.session_state[key]=value
    at.run()
    assert not at.error and not at.exception
    assert 'Gestão de dados' not in at.get('button_group')[0].options
