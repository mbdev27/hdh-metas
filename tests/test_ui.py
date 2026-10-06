from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
import time
import pytest
from streamlit.testing.v1 import AppTest
@pytest.mark.parametrize('page',['01_Visao_Geral','02_Producao','03_Qualidade','04_Consolidacao_Trimestral','05_Monitoramento','06_Governanca_Contratual','07_Gestao_de_Dados'])
def test_pages(page):
    at=AppTest.from_file(ROOT/'pages'/(page+'.py'),default_timeout=40)
    for key,value in dict(authenticated=True,username='adm',role='ADMIN',login_time=time.time()).items():at.session_state[key]=value
    at.run();assert not at.exception
