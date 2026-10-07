"""Period overview and direct navigation to individual indicators."""
import pandas as pd
import plotly.express as px
import streamlit as st
from src.management import production_summary,quality_summary
from src.presentation import chart,present_table,COLORS


def open_indicator():
    contract=st.session_state['summary_contract']
    competence=st.session_state['summary_month']
    choice=st.session_state['summary_open_indicator']
    st.session_state['prod_contract']=contract
    st.session_state['prod_year']='Todos'
    st.session_state['prod_indicator']=choice
    st.session_state['prod_month']=competence
    st.session_state['indicators_section']='Produção assistencial'


def management_summary(p,q):
    st.subheader('Resumo gerencial')
    a,b=st.columns(2)
    contracts=sorted(p.contrato.unique())
    contract=a.selectbox('Contrato do resumo',contracts,index=contracts.index('018/2022') if '018/2022' in contracts else 0,key='summary_contract')
    months=sorted(p[p.contrato==contract].competencia.unique())
    competence=b.selectbox('Competência do resumo',months,index=len(months)-1,key='summary_month')
    production=production_summary(p,contract,competence)
    quality=quality_summary(q,contract,competence)
    counts=production.situacao.value_counts()
    cards=st.columns(4)
    for card,label in zip(cards,['Atingida','Não atingida','Crítico','Sem dados']):
        card.metric({'Atingida':'Metas atingidas','Não atingida':'Metas não atingidas','Crítico':'Indicadores críticos','Sem dados':'Indicadores sem dados'}[label],int(counts.get(label,0)))
    st.caption('Produção: contagem dos indicadores documentados na competência. “Crítico” identifica alcance inferior a 55%; não representa penalidade definitiva. Produções de naturezas diferentes não são somadas.')
    plot=production.rename(columns={'atingimento':'alcance'})
    figure=px.bar(plot,x='alcance',y='nome',color='situacao',orientation='h',color_discrete_map={**COLORS,'Sem dados':'#93a3b4'},labels={'alcance':'Alcance (%)','nome':'Indicador'},title='Alcance das metas no período',hover_data=['realizado','meta_contratual'])
    figure.add_vline(x=100,line_dash='dash',line_color='#24956a',annotation_text='Meta: 100%')
    chart(figure,hovermode='closest')
    gaps=production[production.deficit_percentual>0].sort_values('deficit_percentual',ascending=False).head(5)
    if not gaps.empty:
        st.write('**Principais desvios de produção**')
        for row in gaps.itertuples():
            variation='comparação anterior indisponível' if pd.isna(row.variacao_pp) else f'{row.variacao_pp:+.1f} p.p. em relação ao mês anterior'
            st.write(f'• **{row.nome}**: {row.atingimento:.1f}% de alcance; déficit de {abs(row.diferenca):,.0f} em sua unidade de produção; {variation}.')
    else:st.success('Nenhum déficit identificado nos resultados disponíveis.')
    st.write('**Qualidade e disponibilidade das informações**')
    if quality.empty:st.info('Não há resultados qualitativos documentados nesta competência.')
    else:
        status=quality.groupby('situacao').size().reset_index(name='indicadores')
        chart(px.bar(status,x='situacao',y='indicadores',text='indicadores',color='situacao',color_discrete_map={**COLORS,'Inconsistência':'#d35a64','Sem dados':'#93a3b4','Não aferível':'#8064a2'},labels={'situacao':'Situação','indicadores':'Indicadores'},title='Qualidade e monitoramento — situação no período'))
    missing=int((quality.situacao.isin(['Sem dados','Inconsistência','Não aferível'])).sum()) if not quality.empty else 0
    financial_pending=int(production[production.peso.fillna(0)>0].pontuacao.isna().sum())
    financial_pending+=int(quality[quality.peso.fillna(0)>0].pontuacao.isna().sum()) if not quality.empty else 0
    st.caption(f'Qualidade: {missing} registros sem aferição comparável ou com pendências. Indicadores valorados sem pontuação aferível: {financial_pending}. Pontuação variável total não é estimada com evidências incompletas.')
    with st.expander('Consultar resultados e fontes do resumo'):
        present_table(production,['nome','meta_contratual','realizado','atingimento','situacao','documento_fonte','pagina_fonte'])
        if not quality.empty:present_table(quality,['nome','resultado_texto','situacao','documento_fonte','pagina_fonte'])
    labels=dict(zip(production.indicator_id,production.nome))
    choice=st.selectbox('Abrir indicador do resumo',list(labels),format_func=lambda value:labels[value],key='summary_open_indicator')
    st.button('Ver análise do indicador',key='summary_open',on_click=open_indicator)
