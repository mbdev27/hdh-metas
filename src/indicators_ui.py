"""Indicators ui."""
import streamlit as st
from src.presentation import exports, section
from src.document_ui import rules_view
from src.indicator_views import production_view,quality_view
from src.summary_ui import management_summary

def indicators_page(p,q):
    st.title('Indicadores');st.write('Metas, produção e qualidade com referência à regra de cada período.')
    options=['Resumo gerencial','Produção assistencial','Qualidade e monitoramento','Metas e projeções']
    if st.session_state.get('role')=='ADMIN':options.append('Gestão de dados')
    active=section(options,'indicators_section')
    if active=='Resumo gerencial':management_summary(p,q)
    elif active=='Produção assistencial':production_view(p)
    elif active=='Qualidade e monitoramento':quality_view(q)
    elif active=='Metas e projeções':
        rules_view();st.subheader('PROJEÇÃO FINANCEIRA')
        st.info('Os dados reais disponíveis terminam em março/2026. O valor mensal do 18º TA só se aplica a partir de julho/2026; não é usado retroativamente.')
        st.caption('Projeção exige pontuação completa, valor aplicável e validação das evidências. Não representa valor definitivo a pagar.')
    elif active=='Gestão de dados':
        from src.data_ui import render_data
        render_data()
    exports(p,q,'indicators')


