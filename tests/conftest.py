"""Keep access events from automated tests out of the application history."""
import pytest


@pytest.fixture(autouse=True)
def isolated_access_history(tmp_path,monkeypatch):
    monkeypatch.setenv('ACCESS_HISTORY_PATH',str(tmp_path/'access_history.json'))
