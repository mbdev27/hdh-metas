from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
import time
import pytest
from streamlit.testing.v1 import AppTest
@pytest.mark.parametrize('page',['01_Tela_Inicial','02_Indicadores','03_Instrumentos_de_Gestao','04_Pareceres_CMA','05_Producao_Hospitalar'])
def test_pages(page):
    at=AppTest.from_file(ROOT/'pages'/(page+'.py'),default_timeout=40)
    for key,value in dict(authenticated=True,username='adm',role='ADMIN',login_time=time.time()).items():at.session_state[key]=value
    at.run();assert not at.exception

@pytest.mark.parametrize('page',['01_Tela_Inicial','02_Indicadores','03_Instrumentos_de_Gestao','04_Pareceres_CMA','05_Producao_Hospitalar'])
def test_pages_protected_without_session(page,monkeypatch):
    monkeypatch.delenv('ADMIN_USERNAME',raising=False);monkeypatch.delenv('ADMIN_PASSWORD_HASH',raising=False)
    at=AppTest.from_file(ROOT/'pages'/(page+'.py')).run()
    assert not at.exception
    assert any('Configuração incompleta' in e.value for e in at.error)
    assert not at.dataframe
