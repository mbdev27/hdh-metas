from pathlib import Path
import json
import time
import bcrypt
import pytest
from streamlit.testing.v1 import AppTest
from src.access_history import AccessHistory
from src.restructuring.schema import Actor
ROOT=Path(__file__).resolve().parents[1]


def actor(username='admin',role='ADMIN',expired=False):
    return Actor(username,role,True,time.time()-(3601 if expired else 0))


def test_private_history_persisted_and_no_credentials(tmp_path):
    path=tmp_path/'history.json';history=AccessHistory(path)
    history.record(actor('diretoria','GESTOR'),'LOGIN');history.record(actor('diretoria','GESTOR'),'LOGOUT')
    history.record(actor(expired=True),'SESSION_EXPIRED')
    rows=AccessHistory(path).read(actor())
    assert len(rows)==3
    assert set(rows[0])=={'id','timestamp','username','role','event','session_seconds'}
    assert 'password' not in path.read_text() and 'senha' not in path.read_text()
    for user in [actor('diretoria','GESTOR'),actor('outro','ADMIN'),actor(expired=True),Actor('admin','ADMIN',False,time.time())]:
        with pytest.raises(PermissionError):history.read(user)
    with pytest.raises(PermissionError):history.record(Actor('admin','ADMIN',False,time.time()),'LOGIN')
    with pytest.raises(PermissionError):history.record(actor(),'SESSION_EXPIRED')


def test_login_logout_logged_once_and_failures_not_saved(monkeypatch,tmp_path):
    path=tmp_path/'history.json';monkeypatch.setenv('ACCESS_HISTORY_PATH',str(path))
    monkeypatch.setenv('ADMIN_USERNAME','admin');monkeypatch.setenv('ADMIN_PASSWORD_HASH',bcrypt.hashpw(b'test-history-only',bcrypt.gensalt()).decode())
    at=AppTest.from_file(ROOT/'app.py',default_timeout=40).run()
    at.text_input[0].set_value('unknown');at.text_input[1].set_value('invalid-secret');at.button[0].click().run()
    assert not path.exists()
    at.text_input[0].set_value('admin');at.text_input[1].set_value('test-history-only');at.button[0].click().run();at.run()
    assert len(AccessHistory(path).read(actor()))==1
    assert not at.exception
    next(b for b in at.sidebar.button if b.label=='Sair').click().run()
    rows=AccessHistory(path).read(actor());assert {r['event'] for r in rows}=={'LOGIN','LOGOUT'}
    assert 'test-history-only' not in path.read_text() and 'unknown' not in path.read_text()


def test_expiration_recorded_once(monkeypatch,tmp_path):
    path=tmp_path/'history.json';monkeypatch.setenv('ACCESS_HISTORY_PATH',str(path))
    monkeypatch.setenv('ADMIN_USERNAME','admin');monkeypatch.setenv('ADMIN_PASSWORD_HASH',bcrypt.hashpw(b'test-only',bcrypt.gensalt()).decode())
    at=AppTest.from_file(ROOT/'app.py',default_timeout=40)
    for key,value in dict(authenticated=True,username='admin',role='ADMIN',login_time=time.time()-3602).items():at.session_state[key]=value
    at.run();at.run()
    assert not at.exception
    assert [r['event'] for r in AccessHistory(path).read(actor())]==['SESSION_EXPIRED']
    assert 'authenticated' not in at.session_state


@pytest.mark.parametrize('username,role',[('admin','ADMIN'),('diretoria','GESTOR'),('outro','ADMIN')])
def test_admin_page_access_and_filters(monkeypatch,tmp_path,username,role):
    path=tmp_path/'history.json';monkeypatch.setenv('ACCESS_HISTORY_PATH',str(path))
    history=AccessHistory(path);history.record(actor(),'LOGIN');history.record(actor('diretoria','GESTOR'),'LOGIN')
    at=AppTest.from_file(ROOT/'pages/07_Administracao.py',default_timeout=40)
    for key,value in dict(authenticated=True,username=username,role=role,login_time=time.time()).items():at.session_state[key]=value
    at.run();assert not at.exception and not at.error
    if username=='admin':
        assert len(at.dataframe[0].value)==2
        at.multiselect[0].set_value(['diretoria']).run()
        assert list(at.dataframe[0].value['Usuário'])==['diretoria']
        assert len(at.get('download_button'))==2
    else:
        assert not at.dataframe and not at.get('download_button')
        assert any('apenas para o usuário admin' in warning.value for warning in at.warning)


@pytest.mark.parametrize('username,role,visible',[('admin','ADMIN',True),('diretoria','GESTOR',False),('outro','ADMIN',False)])
def test_administration_navigation_only_for_admin(monkeypatch,username,role,visible):
    import streamlit as st
    captured=[];original=st.navigation
    def navigation(pages,**kwargs):
        captured.extend(page.title for page in pages)
        return original(pages,**kwargs)
    monkeypatch.setattr(st,'navigation',navigation)
    at=AppTest.from_file(ROOT/'app.py',default_timeout=40)
    for key,value in dict(authenticated=True,username=username,role=role,login_time=time.time()).items():at.session_state[key]=value
    at.run()
    assert not at.exception and not at.error
    assert ('Administração' in captured)==visible
