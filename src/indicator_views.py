"""Indicator views."""
import pandas as pd
import plotly.express as px
import streamlit as st
from src.historical import aggregate
from src.presentation import chart, source_name, present_table, filters
from src.charts import production_trend,achievement_chart,quality_numeric_chart,annual_chart
from src.management import comparable_annual
from src.document_ui import foundation

def production_view(p,prefix='prod'):
    work,contract,year=filters(p,prefix)
    choices=sorted(work.indicator_id.unique());lookup=work.drop_duplicates('indicator_id').set_index('indicator_id').nome.to_dict()
    if work.empty:st.info('Não há dados para este recorte.');return
    chosen=st.selectbox('Indicador assistencial',choices,format_func=lambda x:f'{x} · {lookup[x]}',key=prefix+'_indicator');series=work[work.indicator_id==chosen].sort_values('competencia').copy()
    series['situacao']=series.situacao.replace({'CRÍTICO':'Crítico','META ATINGIDA':'Atingida','ATENÇÃO':'Não atingida'})
    selected=st.selectbox('Competência',list(series.competencia),index=len(series)-1,key=prefix+'_month');row=series[series.competencia==selected].iloc[0]
    c=st.columns(4)
    for col,label,value in zip(c,['Meta contratual / referência histórica','Realizado','Alcance da meta pactuada','Pontuação financeira'],[f"{row.meta_contratual:,.0f}".replace(',','.'),'SEM DADOS' if pd.isna(row.realizado) else f"{row.realizado:,.0f}".replace(',','.'),'SEM DADOS' if pd.isna(row.atingimento) else f'{row.atingimento:.2f}%','NÃO AFERÍVEL' if pd.isna(row.pontuacao) else f'{row.pontuacao:.2f} p.p.']):col.metric(label,value)
    st.write('**'+row.situacao+'** · Instrumento da meta: '+source_name(row.instrumento_meta)+(' · p. '+str(int(row.pagina_meta)) if not pd.isna(row.pagina_meta) else ''))
    st.caption(f"Fonte do realizado: {source_name(row.documento_fonte)}, página {row.pagina_fonte}. Meta informada no parecer: {row.meta_reported:.0f}. Déficit/excedente: {'sem dados' if pd.isna(row.diferenca) else f'{row.diferenca:+.0f}' }.")
    if row.divergencia_meta:st.warning('Divergência documental: a meta informada no parecer difere da meta no anexo contratual. Cálculo do alcance usa o anexo; fonte original preservada.')
    if row.observacao and not pd.isna(row.observacao):st.info(row.observacao)
    chart(production_trend(series))
    chart(achievement_chart(series))
    st.caption('Meta = 100%. Faixa financeira máxima = a partir de 85%, conforme regra de cada indicador. Gráficos não preenchem lacunas com zero.')
    present_table(series);foundation(chosen,selected,prefix)
    st.subheader('Consolidação trimestral')
    tri=aggregate(series);present_table(tri)
    alerts=tri[(tri.atingimento<85)&(tri.cobertura=='COMPLETA')]
    if not alerts.empty:st.warning('Desempenho trimestral inferior a 85%. Verificar regra de compensação e providências contratuais. Sem declaração automática de penalidade definitiva.')
    st.caption('Consolidação por contrato e definição do indicador. Períodos parciais são identificados; pontuação exige três meses e uma mesma regra.')
    with st.expander('Matriz mensal do trimestre'):
        matrix=series.copy();matrix['trimestre']=pd.PeriodIndex(matrix.competencia,freq='M').asfreq('Q').astype(str)
        st.dataframe(matrix.pivot(index=['contrato','trimestre'],columns='competencia',values='realizado'),width='stretch')
    st.subheader('Comparação anual — somente meses documentados')
    same=st.checkbox('Comparar os mesmos meses entre anos',key=prefix+'_same_months')
    comparison=comparable_annual(series,same)
    annual=aggregate(comparison,'Y');chart(annual_chart(annual));present_table(annual)
    if same:st.caption('Comparação limitada aos meses representados no ano mais recente do recorte. Contratos e definições históricas permanecem separados; a tabela informa a cobertura.')


def quality_view(q,prefix='quality'):
    work,contract,year=filters(q,prefix)
    ids=sorted(work.indicator_id.unique());lookup=work.drop_duplicates('indicator_id').set_index('indicator_id').nome.to_dict()
    if work.empty:st.info('Não há dados para este recorte.');return
    chosen=st.selectbox('Indicador de qualidade / monitoramento',ids,format_func=lambda x:lookup[x],key=prefix+'_indicator');series=work[work.indicator_id==chosen].sort_values('competencia')
    st.info('Resultados qualitativos mensais transcritos dos pareceres. Não reconstruímos numeradores ou denominadores ausentes. Pontuação total não é aferível quando faltam evidências.')
    cards=st.columns(3)
    cards[0].metric('Meses documentados',len(series))
    cards[1].metric('Meses sem dados',int((series.status_dado=='SEM DADOS').sum()))
    cards[2].metric('Inconsistências na fonte',int((series.status_dado=='INCONSISTÊNCIA NA FONTE').sum()))
    if series.valor.notna().any():
        chart(quality_numeric_chart(series))
    else:
        categorical=series.copy()
        categorical['resultado_visual']=categorical.resultado_texto.fillna('Sem dados').replace('', 'Sem dados')
        chart(px.scatter(categorical,x='competencia',y='resultado_visual',color='status_dado',symbol='status_dado',color_discrete_map={'INFORMADO':'#24956a','SEM DADOS':'#93a3b4','INCONSISTÊNCIA NA FONTE':'#d35a64'},title='Histórico dos resultados informados',labels={'competencia':'Competência','resultado_visual':'Resultado publicado','status_dado':'Situação dos dados'}))
        st.caption('Resultados textuais são apresentados como categorias, sem conversão em pontuação ou valores numéricos.')
    status_counts=series.groupby('status_dado').size().reset_index(name='meses')
    chart(px.bar(status_counts,x='status_dado',y='meses',text='meses',title='Disponibilidade e qualidade das informações',labels={'status_dado':'Situação dos dados','meses':'Meses'}))
    with st.expander('Consultar resultado e fonte por mês'):
        comp=st.selectbox('Competência do resultado',series.competencia.tolist(),key=prefix+'_source_month')
        result=series[series.competencia==comp].iloc[0]
        st.write('**Resultado publicado:** '+str(result.resultado_texto or 'Sem dados'))
        st.write('**Fonte:** '+source_name(result.documento_fonte)+' · página '+str(result.pagina_fonte))
    if (series.status_dado=='INCONSISTÊNCIA NA FONTE').any():st.warning('A fonte contém percentuais inconsistentes. Os valores foram preservados e sinalizados; não entram no cálculo financeiro.')
    st.caption('PONTUAÇÃO MENSAL · Projeções trimestrais qualitativas não são recalculadas sem evidências suficientes. Ocupação e prontuários sem peso próprio não compõem a parte variável.')
    foundation(series.iloc[-1].rule_indicator_id,series.iloc[-1].competencia,prefix)


