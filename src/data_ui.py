import logging
import pandas as pd
import plotly.express as px
import streamlit as st
from src.auth import require_login
from src.theme import header
from src.data_loader import mocks,read_upload,normalize
from src.data_validation import validate,PRODUCTION,QUALITY
from src.calculations import monthly,quarter
from src.contract_engine import ContractEngine
from src.contract_registry import load,inventory,duplicates
from src.exports import workbook,csv_bytes
from src.formatting import currency
from src.utils import DEMAND_STATUSES

def show_stats(stats):
    columns=st.columns(4)
    for col,label,key in zip(columns,['Registros recebidos','Registros válidos','Registros rejeitados','Campos sem informação'],['linhas_carregadas','linhas_validas','linhas_rejeitadas','campos_faltantes']):col.metric(label,stats[key])

def show_report(report):
    if report.empty:return
    with st.expander('Pendências de qualidade dos dados'):
        st.dataframe(report.rename(columns={'linha':'Registro','campo':'Campo','nivel':'Tipo','mensagem':'Descrição','base':'Conjunto'}),hide_index=True,width='stretch')

def render_data():
    if st.session_state.get("role")!="ADMIN":
        st.info("A importação de dados está disponível para o administrador.");return
    from src.portal import present_table
    if 'production' not in st.session_state:
        p,q=mocks();p,rp,sp=validate(p,'producao');q,rq,sq=validate(q,'qualidade')
        st.session_state.update(production=p,quality=q,reports=pd.concat([rp.assign(base='Produção'),rq.assign(base='Qualidade')]),data_stats=[sp,sq],import_audit=[])
    p=st.session_state.production;q=st.session_state.quality
    month=st.selectbox('Competência do cenário importado',sorted(p.competencia.unique()),key='import_month')
    t=monthly(p,q,month)
    st.info('ÁREA DE SIMULAÇÃO / IMPORTAÇÃO: os uploads não sobrescrevem as séries documentais CMA. Dados somente na sessão.')
    st.subheader('Gestão de Dados')
    for label,stats in zip(['Produção','Qualidade'],st.session_state.data_stats):
        st.write('**'+label+'**');show_stats(stats)
    show_report(st.session_state.reports)
    kind=st.selectbox('Conjunto de destino',['producao','qualidade']);encoding=st.selectbox('Codificação',['utf-8','latin-1','cp1252'])
    upload=st.file_uploader('CSV, XLSX, DBF ou Parquet — somente dados agregados, sem identificação pessoal',type=['csv','xlsx','dbf','parquet'])
    if upload:
        try:
            raw=read_upload(upload.getvalue(),upload.name,encoding)
            st.write('LEITURA — prévia original');st.dataframe(raw.head())
            mapping={};targets=PRODUCTION if kind=='producao' else QUALITY
            with st.expander('MAPEAMENTO — preservar nomes originais'):
                for col in raw.columns:
                    default=normalize(pd.DataFrame(columns=[col]))[0].columns[0]
                    opts=[default]+[x for x in targets if x!=default]
                    mapping[col]=st.selectbox(str(col),opts,key='map_'+kind+str(col))
            normalized,metadata=normalize(raw,mapping)
            if any(c not in targets for c in normalized.columns):raise ValueError('Colunas extras não autorizadas. Remova campos fora do esquema agregado antes de importar.')
            clean,report,stats=validate(normalized,kind)
            st.subheader('Resultado da validação');show_stats(stats);show_report(report);st.write('PRÉVIA — linhas válidas');st.dataframe(clean.head(50))
            if stats['linhas_rejeitadas'] or (report.nivel=='ERRO').any():st.error('Arquivo inválido. Corrija todos os erros antes da consolidação.')
            elif not clean.empty:
                confirmation=st.checkbox('Confirmo o conjunto, o mapeamento e a substituição explícita das competências coincidentes.')
                if st.button('Confirmar consolidação',disabled=not confirmation):
                    key='production' if kind=='producao' else 'quality';current=st.session_state[key]
                    merged=pd.concat([current[~current.competencia.isin(clean.competencia)],clean],ignore_index=True).sort_values('competencia')
                    st.session_state[key]=merged
                    st.session_state.import_audit.append({'arquivo':upload.name,'mapeamento':metadata,'linhas':len(clean),'data':pd.Timestamp.now().isoformat(),'usuario':st.session_state.username})
                    st.session_state.reports=pd.concat([st.session_state.reports,report.assign(base=kind)],ignore_index=True);st.success('Consolidado na sessão. Exporte para preservar os resultados.');st.rerun()
        except Exception:
            logging.getLogger(__name__).exception('Falha ao importar base')
            st.error('Não foi possível importar o arquivo. Confira o formato, a codificação e as colunas e tente novamente.')
    st.subheader('Justificativas de demanda — sem dispensa automática')
    indicator=st.selectbox('Indicador',t.indicador);status=st.selectbox('Status',DEMAND_STATUSES);note=st.text_area('Justificativa agregada, sem dados pessoais')
    if st.button('Registrar justificativa'):
        st.session_state.setdefault('justifications',[]).append({'competencia':month,'indicador':indicator,'status':status,'justificativa':note,'usuario':st.session_state.username});st.success('Registro de sessão salvo. Pontuação preservada; validação depende da Contratante.')
    if st.session_state.get('justifications'):st.dataframe(pd.DataFrame(st.session_state.justifications).rename(columns={'competencia':'Competência','indicador':'Indicador','status':'Situação','justificativa':'Justificativa','usuario':'Responsável'}),hide_index=True)
    if st.session_state.import_audit:
        with st.expander('Histórico de importações'):
            st.dataframe(pd.DataFrame(st.session_state.import_audit)[['arquivo','linhas','data']].rename(columns={'arquivo':'Arquivo','linhas':'Registros','data':'Importado em'}),hide_index=True)

    st.download_button('Exportar base de produção da sessão',csv_bytes(st.session_state.production),'producao_sessao.csv',key='exp_prod')
    st.download_button('Exportar base de qualidade da sessão',csv_bytes(st.session_state.quality),'qualidade_sessao.csv',key='exp_qual')
    tables={'Resumo':t,'Produção':st.session_state.production,'Qualidade':st.session_state.quality,'Trimestre':quarter(st.session_state.production,st.session_state.quality,pd.Period(month,freq='Q'))[0],'Monitoramento':t[t.grupo=='monitoramento'],'Qualidade dos Dados':st.session_state.reports,'Regras Contratuais':pd.DataFrame(load('demo_rules.yaml')['rules']).astype(str)}
    st.download_button('Exportar simulação XLSX',workbook(tables),'simulacao_hdh.xlsx',key='exp_sim')
    with st.expander('Dashboard do cenário de simulação',expanded=False):
        st.info('DADOS SIMULADOS / IMPORTADOS NA SESSÃO — não correspondem ao histórico documental CMA.')
        present_table(t)
        st.plotly_chart(px.bar(t[t.grupo!='monitoramento'],x='indicador',y='pontuacao',color='grupo'),width='stretch')
        st.caption('Pesos máximos: 20 p.p. quantitativos + 10 p.p. qualitativos. Meta = 100%; faixa máxima de produção a partir de 85%.')
        value=ContractEngine().monthly_value(month)
        if value is not None:
            projection=t[t.grupo!='monitoramento'][['indicador','peso','pontuacao']].copy()
            projection['valor_maximo']=value*projection.peso/100
            projection['valor_projetado']=value*projection.pontuacao/100
            st.write('PROJEÇÃO FINANCEIRA — cenário da sessão');st.dataframe(projection,hide_index=True)
            st.caption('Não representa valor definitivo a pagar. Dados e regras do cenário devem ser validados antes de uso institucional.')
        else:st.caption('Sem valor financeiro aplicável validado para esta competência. Valor do 18º TA não retroativo.')
