import streamlit as st
from src.auth import require_login
from src.theme import apply_theme
from src.safe_ui import run_safely
st.set_page_config(page_title='HDH Metas',page_icon='🏥',layout='wide',initial_sidebar_state='expanded' if st.session_state.get('authenticated') else 'collapsed')
apply_theme()
require_login()
pages=[st.Page('pages/01_Tela_Inicial.py',title='Tela inicial',icon=':material/home:',default=True),st.Page('pages/02_Indicadores.py',title='Indicadores',icon=':material/monitoring:'),st.Page('pages/03_Instrumentos_de_Gestao.py',title='Instrumentos de gestão',icon=':material/folder_open:'),st.Page('pages/04_Pareceres_CMA.py',title='Pareceres CMA',icon=':material/description:'),st.Page('pages/05_Producao_Hospitalar.py',title='Produção Hospitalar',icon=':material/local_hospital:'),st.Page('pages/06_Indicadores_de_Reestruturacao.py',title='Indicadores de reestruturação',icon=':material/fact_check:')]
if st.session_state.get('role')=='ADMIN' and st.session_state.get('username')=='admin':
    pages.append(st.Page('pages/07_Administracao.py',title='Administração',icon=':material/admin_panel_settings:'))
run_safely(st.navigation(pages,position='sidebar').run)
