"""JSON file configuration. Local files are not durable storage on Community Cloud."""
import os
from pathlib import Path
import streamlit as st
from src.restructuring.repository import Repository,FileStore


def storage_path():
    try:settings=dict(st.secrets.get('restructuring',{}))
    except Exception:settings={}
    configured=os.getenv('RESTRUCTURING_STORAGE_PATH') or settings.get('storage_path')
    path=Path(configured or 'data/private/reestruturacao.json').expanduser()
    if path.suffix.lower()!='.json':raise ValueError('Configure um arquivo de registros com extensão .json.')
    return str(path.resolve())


@st.cache_resource(show_spinner=False)
def persistent_repository(path):
    return Repository(FileStore(path))
