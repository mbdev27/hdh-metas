"""Keep technical failures in server logs, with a useful message for the visitor."""
import logging
import streamlit as st

def run_safely(callback,*args,**kwargs):
    try:return callback(*args,**kwargs)
    except Exception:
        logging.getLogger(__name__).exception('Falha ao apresentar página')
        st.error('Não foi possível carregar esta área. Atualize a página e tente novamente. Se o problema continuar, informe ao responsável pelo painel.')
