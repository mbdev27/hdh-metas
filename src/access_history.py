"""Minimal access events in JSON; read access is restricted to the admin account."""
from datetime import datetime,timezone
import logging
import math
import os
from pathlib import Path
import uuid
import streamlit as st
from src.restructuring.file_store import FileStore
from src.restructuring.schema import Actor,current_actor

EVENTS={'LOGIN':'Login realizado','LOGOUT':'Saída realizada','SESSION_EXPIRED':'Sessão expirada'}


def require_admin(actor):
    actor.require()
    if actor.username!='admin' or actor.role!='ADMIN':raise PermissionError('Histórico de acesso restrito ao usuário admin.')


class AccessHistory:
    def __init__(self,path):self.store=FileStore(path)

    def record(self,actor,event):
        if event not in EVENTS:raise ValueError('Evento de acesso inválido.')
        if event=='SESSION_EXPIRED':
            if not actor.authenticated or not actor.username or actor.role not in ('ADMIN','GESTOR','LEITURA') or time_elapsed(actor)<3600:raise PermissionError('Sessão expirada não comprovada.')
        else:actor.require()
        if not math.isfinite(actor.login_time):raise ValueError('Data de sessão inválida.')
        entry={'id':str(uuid.uuid4()),'timestamp':datetime.now(timezone.utc).isoformat(),
               'username':actor.username,'role':actor.role,'event':event,
               'session_seconds':None if event=='LOGIN' else round(time_elapsed(actor))}
        with self.store.transaction() as state:
            state['entries'].append(entry);state['initialized']=True

    def read(self,actor):
        require_admin(actor)
        return sorted(self.store.state()['entries'],key=lambda row:row['timestamp'],reverse=True)


def time_elapsed(actor):
    return max(0,datetime.now(timezone.utc).timestamp()-actor.login_time)


def history_path():
    try:settings=dict(st.secrets.get('access_history',{}))
    except Exception:settings={}
    path=Path(os.getenv('ACCESS_HISTORY_PATH') or settings.get('storage_path','data/private/access_history.json')).expanduser()
    if path.suffix.lower()!='.json':raise ValueError('Histórico exige arquivo JSON.')
    return path.resolve()


def log_session_event(event):
    """Log only after successful authentication; never store credentials or unknown input."""
    try:AccessHistory(history_path()).record(current_actor(st.session_state),event)
    except Exception:
        # Logging failure must not prevent login/logout; do not log credentials or paths.
        logging.getLogger(__name__).error('Não foi possível registrar evento no histórico de acesso.')
        st.session_state['access_history_notice']=True
