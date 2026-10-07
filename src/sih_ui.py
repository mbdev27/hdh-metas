import json
import pandas as pd
import plotly.express as px
import streamlit as st
from src.sih import load_sih,monthly_series,NON_ADDITIVE,measure_unit
from src.contract_registry import ROOT
from src.presentation import chart,section
from src.theme import sidebar_notice
from src.exports import csv_bytes
from src.reporting import sih_workbook


def formatted(value,unit):
    if value is None or pd.isna(value):return 'SEM DADO'
    digits=2 if unit in ['R$','%'] else 1 if value%1 else 0
    text=f'{value:,.{digits}f}'.replace(',','_').replace('.',',').replace('_','.')
    return ('R$ ' if unit=='R$' else '')+text+('%' if unit=='%' else '')


def annual_for_selection(data,selected,measure,dimension,category='Total'):
    original=monthly_series(data);original=original[(original.medida==measure)&(original.dimensao==dimension)&(original.categoria==category)]
    work=selected[(selected.medida==measure)&(selected.dimensao==dimension)&(selected.categoria==category)]
    rows=[]
    for year,group in work.groupby('ano'):
        full=set(group.competencia)==set(original[original.ano==year].competencia)
        source=data[(data.tipo_linha=='ano_publicado')&(data.ano==year)&(data.medida==measure)&(data.dimensao==dimension)&(data.categoria==category)]
        value=source.iloc[0].valor if full and not source.empty else None if measure in NON_ADDITIVE or group.valor.isna().any() else group.valor.sum()
        rows.append(dict(ano=int(year),valor=value,meses=group.competencia.nunique(),apuracao='Valor anual publicado no CSV' if full else 'Não calculado: taxa/média não aditiva' if measure in NON_ADDITIVE else 'Soma dos meses selecionados',cobertura='ANO COMPLETO' if group.competencia.nunique()==12 else 'ANO PARCIAL',source_id=group.iloc[0].source_id))
    return pd.DataFrame(rows)


def metric_series(selected,measure,dimension='Caráter atendimento',category='Total'):
    return selected[(selected.medida==measure)&(selected.dimensao==dimension)&(selected.categoria==category)].sort_values('competencia')


def trend_and_annual(data,selected,measure,dimension='Caráter atendimento',key='metric'):
    series=metric_series(selected,measure,dimension)
    unit=measure_unit(measure)
    chart(px.line(series,x='competencia',y='valor',markers=True,title=measure+' — evolução mensal',labels={'competencia':'Mês do atendimento','valor':unit},color_discrete_sequence=['#176fa1']))
    annual=annual_for_selection(data,selected,measure,dimension)
    if not annual.empty:
        chart(px.bar(annual,x='ano',y='valor',color='cobertura',title=measure+' — comparação anual',labels={'valor':unit,'ano':'Ano'},color_discrete_map={'ANO COMPLETO':'#176fa1','ANO PARCIAL':'#7ca8c7'}))
        st.dataframe(annual,hide_index=True,width='stretch')
    st.caption('Taxas e médias anuais são valores publicados no CSV, sem soma ou média simples dos meses. Recortes que não correspondem ao ano disponível não recebem taxa anual calculada.')
    with st.expander('Tabela mensal — '+measure):st.dataframe(series[['competencia','categoria','valor','valor_original','source_id','linha_fonte']],hide_index=True,width='stretch')


def render_sih():
    sidebar_notice()
    st.title('Produção Hospitalar')
    st.write('Produção registrada no SIH/SUS para o Hospital Dom Helder Câmara — CNES **6559379**.')
    st.markdown('**Fonte:** [DATASUS / TabNet — Ministério da Saúde](https://tabnet.datasus.gov.br/) · **Extração pelo solicitante: 06/10/2026** · **Recorte: janeiro/2020 a julho/2026**.')
    data,metadata=load_sih();all_months=monthly_series(data)
    st.info('Dados públicos agregados por mês do atendimento. AIHs aprovadas não equivalem automaticamente a saídas hospitalares, internações ou procedimentos das metas contratuais. Valores SIH não são repasses do Contrato de Gestão.')
    a,b=st.columns([1,2]);years=['Todos']+sorted(all_months.ano.dropna().astype(int).unique().tolist())
    year=a.selectbox('Ano de atendimento',years,key='sih_year')
    months=sorted(all_months.competencia.unique())
    available=months if year=='Todos' else [m for m in months if m.startswith(str(year))]
    start,end=b.select_slider('Período de atendimento',options=available,value=(available[0],available[-1]),key='sih_period_'+str(year))
    selected=monthly_series(data,start,end)
    latest=end;aih=metric_series(selected,'AIH aprovadas');value=metric_series(selected,'Valor total');deaths=metric_series(selected,'Óbitos');rate=metric_series(selected,'Taxa mortalidade')
    c=st.columns(4)
    c[0].metric('AIHs aprovadas no recorte',formatted(None if aih.valor.isna().any() else aih.valor.sum(),'AIHs'))
    c[1].metric('Valor SIH aprovado no recorte',formatted(None if value.valor.isna().any() else value.valor.sum(),'R$'))
    c[2].metric('Óbitos informados no recorte',formatted(None if deaths.valor.isna().any() else deaths.valor.sum(),'óbitos'))
    c[3].metric('Mortalidade no último mês',formatted(rate.iloc[-1].valor,'%'))
    st.caption(f'Período selecionado: {start} a {end} · {selected.competencia.nunique()} meses · Mortalidade do card: {latest}. Não calculada mortalidade acumulada sem denominador apropriado.')
    active=section(['Visão geral','Perfil assistencial','Valores e permanência','Óbitos e mortalidade','Fontes e tabelas'],'sih_section')
    if active=='Visão geral':
        trend_and_annual(data,selected,'AIH aprovadas')
        st.caption('AIHs são autorizações aprovadas no SIH; não representam contagem de todos os procedimentos secundários realizados.')
    elif active=='Perfil assistencial':
        dimension=st.selectbox('Classificação da produção',['Caráter atendimento','Grupo procedimento','Subgrupo proced.'],key='sih_dimension')
        series=selected[(selected.medida=='AIH aprovadas')&(selected.dimensao==dimension)&(selected.categoria!='Total')]
        table=series.pivot(index='competencia',columns='categoria',values='valor')
        cats=sorted(series.categoria.unique());chosen=st.multiselect('Categorias para comparar',cats,default=cats if dimension=='Grupo procedimento' else cats[:min(len(cats),5)],key='sih_categories_'+dimension)
        if chosen:chart(px.line(series[series.categoria.isin(chosen)],x='competencia',y='valor',color='categoria',markers=True,title='AIHs aprovadas por '+dimension.lower(),labels={'valor':'AIHs aprovadas','competencia':'Mês do atendimento'}))
        st.dataframe(table,width='stretch');st.caption('Total excluído da comparação de categorias para evitar dupla contagem. Símbolos sem valor numérico permanecem ausentes. Grupos SIGTAP do SIH não são automaticamente equivalentes às categorias contratuais de cirurgia.')
    elif active=='Valores e permanência':
        measures=sorted(set(selected.medida)-{'AIH aprovadas','Óbitos','Taxa mortalidade'})
        measure=st.selectbox('Medida de valores ou permanência',measures,key='sih_value_measure')
        trend_and_annual(data,selected,measure,key='financial')
        st.caption('Valor total e seus componentes hospitalares/profissionais são medidas distintas: não somar os componentes novamente ao valor total. Valor médio de internação é publicado na fonte; não é obtido dividindo automaticamente por AIHs.')
    elif active=='Óbitos e mortalidade':
        measure=st.radio('Medida assistencial',['Óbitos','Taxa mortalidade'],horizontal=True,key='sih_mortality_measure')
        trend_and_annual(data,selected,measure,key='mortality')
        st.caption('Mortalidade SIH é a taxa publicada no sistema. Não equivale à taxa de revisão de óbitos institucional, nem constitui uma meta financeira adicional.')
    elif active=='Fontes e tabelas':
        st.warning('Os CSVs também contêm dezembro/2019. Esse mês está preservado nos originais e nas observações, mas fora do recorte padrão 2020–2026. Totais gerais originais podem incluí-lo.')
        st.info('Foram recebidos 12 arquivos, com 11 conteúdos únicos. A segunda exportação de mortalidade é idêntica por SHA-256 e não é contada novamente.')
        st.caption('Notas da fonte: dados referentes aos últimos seis meses sujeitos a atualização. “-”, “...” e campos vazios são conservados como símbolos originais, sem conversão automática para zero.')
        byid={m['source_id']:m for m in metadata};chosen=st.selectbox('Arquivo de origem',list(byid),format_func=lambda x:byid[x]['titulo']+' · '+byid[x]['nome_arquivo'],key='sih_source')
        meta=byid[chosen]
        st.write('**'+meta['titulo']+'**')
        st.caption('CNES '+meta['cnes']+' · Fonte: Ministério da Saúde — SIH/SUS · Extração: 06/10/2026')
        st.download_button('Baixar CSV original TabNet',(ROOT/meta['arquivo_original']).read_bytes(),meta['nome_arquivo'],mime='text/csv',key='sih_original')
        canonical=meta['duplicate_of'] or chosen;original=data[data.source_id==canonical]
        st.dataframe(original[['medida','dimensao','competencia','ano','categoria','valor','valor_original']].rename(columns={'medida':'Medida','dimensao':'Classificação','competencia':'Competência','ano':'Ano','categoria':'Categoria','valor':'Valor','valor_original':'Valor na fonte'}),hide_index=True,width='stretch')
    with st.expander('Exportar a produção hospitalar'):
        if not st.checkbox('Preparar arquivos para download',key='sih_prepare_exports'):return
        st.download_button('CSV — dados mensais do recorte',csv_bytes(selected),'hdh_sih_mensal.csv',key='sih_export_csv')
        st.download_button('XLSX — dados SIH e fontes',sih_workbook(data,selected,metadata),'hdh_sih.xlsx',key='sih_export_xlsx')
