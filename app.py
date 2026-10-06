import streamlit as st
from src.auth import require_login
st.set_page_config(page_title='HDH Metas',page_icon='🏥',layout='wide')
require_login()
pages=[st.Page('pages/01_Visao_Geral.py',title='Visão Geral'),st.Page('pages/02_Producao.py',title='Produção'),st.Page('pages/03_Qualidade.py',title='Qualidade'),st.Page('pages/04_Consolidacao_Trimestral.py',title='Consolidação Trimestral'),st.Page('pages/05_Monitoramento.py',title='Monitoramento'),st.Page('pages/06_Governanca_Contratual.py',title='Governança Contratual'),st.Page('pages/07_Gestao_de_Dados.py',title='Gestão de Dados')]
st.navigation(pages).run()
