from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
import bcrypt
from streamlit.testing.v1 import AppTest
from src.auth import verify

def test_hash_and_login(monkeypatch):
    h=bcrypt.hashpw(b'test-only-password',bcrypt.gensalt()).decode()
    assert verify('adm','test-only-password','adm',h)
    assert not verify('adm','wrong','adm',h)
    monkeypatch.setenv('ADMIN_USERNAME','adm');monkeypatch.setenv('ADMIN_PASSWORD_HASH',h)
    at=AppTest.from_file(ROOT/'app.py',default_timeout=40).run()
    assert not at.exception
    at.text_input[0].set_value('adm');at.text_input[1].set_value('test-only-password');at.button[0].click().run()
    assert at.session_state['authenticated'] is True
    assert not at.exception
    next(b for b in at.sidebar.button if b.label=='Sair').click().run()
    assert 'authenticated' not in at.session_state

def test_missing_config(monkeypatch):
    monkeypatch.delenv('ADMIN_USERNAME',raising=False);monkeypatch.delenv('ADMIN_PASSWORD_HASH',raising=False)
    at=AppTest.from_file(ROOT/'app.py').run();assert not at.exception
    assert any('Configuração incompleta' in e.value for e in at.error)

def test_lockout(monkeypatch):
    monkeypatch.setenv('ADMIN_USERNAME','adm');monkeypatch.setenv('ADMIN_PASSWORD_HASH',bcrypt.hashpw(b'test-only',bcrypt.gensalt()).decode())
    at=AppTest.from_file(ROOT/'app.py').run()
    for _ in range(5):
        at.text_input[0].set_value('adm');at.text_input[1].set_value('wrong');at.button[0].click().run()
    assert at.session_state['blocked_until']>0
