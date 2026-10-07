"""Plot builders independent from page widgets, with explicit contractual references."""
import pandas as pd
import plotly.express as px

COLORS={'Atingida':'#24956a','Não atingida':'#d29520','Crítico':'#d35a64','SEM DADOS':'#93a3b4'}


def production_trend(series):
    work=series.rename(columns={'realizado':'Realizado','meta_contratual':'Meta'})
    figure=px.line(work,x='competencia',y=['Realizado','Meta'],markers=True,color_discrete_sequence=['#1675b8','#6c9bad'],labels={'value':'Quantidade','competencia':'Competência','variable':'Série'},title='Produção mensal e meta do período')
    figure.update_traces(connectgaps=False)
    return figure


def achievement_chart(series):
    figure=px.bar(series,x='competencia',y='atingimento',color='situacao',color_discrete_map=COLORS,labels={'atingimento':'Alcance (%)','competencia':'Competência'},title='Alcance de meta pactuada')
    figure.add_hline(y=100,line_dash='dash',line_color='#24956a',annotation_text='Meta: 100%',annotation_position='top left')
    figure.add_hline(y=85,line_dash='dot',line_color='#146bb0',annotation_text='Faixa financeira máxima: 85%',annotation_position='bottom left')
    return figure


def quality_numeric_chart(series):
    work=series.copy()
    work['Meta']=pd.to_numeric(work.meta_aplicada,errors='coerce')
    work=work.rename(columns={'valor':'Resultado'})
    fields=['Resultado','Meta'] if work.Meta.notna().any() else ['Resultado']
    figure=px.line(work,x='competencia',y=fields,markers=True,labels={'value':'Valor informado','competencia':'Competência','variable':'Série'},title='Resultado mensal e meta identificada',hover_data=['resultado_texto','status_dado'])
    figure.update_traces(connectgaps=False)
    return figure


def annual_chart(annual,title='Produção e meta acumulada no ano'):
    frame=annual.rename(columns={'realizado':'Realizado','meta_acumulada':'Meta acumulada'})
    figure=px.bar(frame,x='periodo',y=['Realizado','Meta acumulada'],barmode='group',facet_col='contrato',labels={'periodo':'Ano','value':'Quantidade','variable':'Série','contrato':'Contrato'},hover_data=['meses_presentes','cobertura'],title=title)
    return figure
