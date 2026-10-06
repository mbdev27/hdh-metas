from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
import bcrypt
from streamlit.testing.v1 import AppTest
from src.auth import verify

def test_hash_and_login(monkeypatch):
    h=bcrypt.hashpw(b'test-only-password',bcrypt.gensalt()).decode()
    assert verify('admin','test-only-password','admin',h)
    assert not verify('admin','wrong','admin',h)
    monkeypatch.setenv('ADMIN_USERNAME','admin');monkeypatch.setenv('ADMIN_PASSWORD_HASH',h)
    at=AppTest.from_file(ROOT/'app.py',default_timeout=40).run()
    assert not at.exception
    at.text_input[0].set_value('admin');at.text_input[1].set_value('test-only-password');at.button[0].click().run()
    assert at.session_state['authenticated'] is True
    assert not at.exception
    next(b for b in at.sidebar.button if b.label=='Sair').click().run()
    assert 'authenticated' not in at.session_state

def test_missing_config(monkeypatch):
    monkeypatch.delenv('ADMIN_USERNAME',raising=False);monkeypatch.delenv('ADMIN_PASSWORD_HASH',raising=False)
    at=AppTest.from_file(ROOT/'app.py').run();assert not at.exception
    assert any('Configuração incompleta' in e.value for e in at.error)

def test_lockout(monkeypatch):
    monkeypatch.setenv('ADMIN_USERNAME','admin');monkeypatch.setenv('ADMIN_PASSWORD_HASH',bcrypt.hashpw(b'test-only',bcrypt.gensalt()).decode())
    at=AppTest.from_file(ROOT/'app.py').run()
    for _ in range(5):
        at.text_input[0].set_value('admin');at.text_input[1].set_value('wrong');at.button[0].click().run()
    assert at.session_state['blocked_until']>0

def test_original_username_migrated_without_password_change(monkeypatch):
    from src.auth import credentials
    hashed=bcrypt.hashpw(b'test-only-migration',bcrypt.gensalt()).decode()
    monkeypatch.setenv('ADMIN_USERNAME','adm');monkeypatch.setenv('ADMIN_PASSWORD_HASH',hashed)
    username,current_hash=credentials()
    assert username=='admin' and current_hash==hashed
    assert verify('admin','test-only-migration',username,current_hash)
    assert not verify('adm','test-only-migration',username,current_hash)

def test_login_hides_sidebar(monkeypatch):
    monkeypatch.setenv('ADMIN_USERNAME','admin');monkeypatch.setenv('ADMIN_PASSWORD_HASH',bcrypt.hashpw(b'test-only',bcrypt.gensalt()).decode())
    at=AppTest.from_file(ROOT/'app.py').run()
    assert not at.exception
    assert not at.sidebar.button
    assert any('stSidebar' in m.value and 'display:none' in m.value for m in at.markdown)
