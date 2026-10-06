import json
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

def context():
    require_login();header()
    if 'production' not in st.session_state:
        p,q=mocks();p,rp,sp=validate(p,'producao');q,rq,sq=validate(q,'qualidade')
        st.session_state.update(production=p,quality=q,reports=pd.concat([rp.assign(base='Produção'),rq.assign(base='Qualidade')]),data_stats=[sp,sq],import_audit=[])
    p=st.session_state.production;q=st.session_state.quality
    choices=sorted(set(p.competencia)|set(q.competencia))
    month=st.sidebar.selectbox('Competência',choices,index=len(choices)-1)
    year=st.sidebar.selectbox('Ano da tendência',sorted({x[:4] for x in choices},reverse=True))
    table=monthly(p,q,month)
    st.caption(f"Competência: {month} · Trimestre: {pd.Period(month,freq='Q')} · Ruleset: {load('contract_rules.yaml')['ruleset']}")
    st.caption('Máximo Quantitativo: 20 p.p. · Máximo Qualitativo: 10 p.p. · Máximo Total: 30 p.p.')
    st.warning('Necessita validação documental: sem anexos auditados, vigências das metas não comprovadas. Cálculos exclusivamente demonstrativos.')
    return p,q,month,year,table

def foundation(table,month):
    st.subheader('Fundamentação contratual')
    for row in table.to_dict('records'):
        with st.expander('Fundamentação contratual · '+row['indicador']+' · '+row['nome']):
            r=ContractEngine().resolve(row['indicador'],month,True)
            st.json(r)
            st.caption('Regra anterior: anexo original do 8º TA, conteúdo não fornecido. Histórico de 4.286 consultas citado no prompt, sem vigência comprovada. Não aplicado.')

def total(table,group):
    values=table[table.grupo==group].pontuacao
    return None if values.isna().any() else float(values.sum())
def display_points(value):return 'NÃO AFERÍVEL' if value is None else f'{value:.2f} p.p.'

def render(page):
    p,q,month,year,t=context();engine=ContractEngine();value=engine.monthly_value(month)
    if page=='overview':
        st.subheader('Visão Geral')
        st.write('Valor mensal contratual aplicável: '+currency(value))
        qt=total(t,'quantitativo');ql=total(t,'qualitativo')
        cols=st.columns(4)
        quantities=t[t.grupo=='quantitativo']
        rate=None if quantities.realizado.isna().any() else quantities.realizado.sum()/pd.to_numeric(quantities.meta).sum()*100
        cols[0].metric('Atingimento Quantitativo', 'SEM DADOS' if rate is None else f'{rate:.1f}%');cols[1].metric('Pontuação Quantitativa',display_points(qt));cols[2].metric('Pontuação Qualitativa',display_points(ql));cols[3].metric('Pontuação Variável Total',display_points(None if qt is None or ql is None else qt+ql))
        st.caption('Atingimento agregado é descritivo; a pontuação avalia cada indicador individualmente.')
        cols=st.columns(4)
        for c,label,count in zip(cols,['Indicadores Atingidos','Indicadores em Atenção','Indicadores Críticos','Indicadores sem Dados'],[(t.situacao=='META ATINGIDA').sum(),((t.situacao=='META NÃO ATINGIDA') & (t.pontuacao.fillna(0)>0)).sum(),((t.situacao!='META ATINGIDA') & (t.pontuacao==0)).sum(),t.pontuacao.isna().sum()]):c.metric(label,int(count))
        st.plotly_chart(px.bar(t[t.grupo!='monitoramento'],x='indicador',y='pontuacao',color='grupo'),width='stretch')
        st.subheader('Condições Financeiras do Contrato')
        st.write('16º TA: estrutura de pagamento com 70% e 30% restantes, conforme prompt. Não representa a valoração dos indicadores.')
        st.write('Valoração de desempenho: 20% quantitativos + 10% qualitativos = 30% de parte variável.')
        st.subheader('PROJEÇÃO FINANCEIRA')
        if value is not None:
            projection=t[t.grupo!='monitoramento'][['indicador','peso','pontuacao']].copy();projection['valor_maximo']=value*projection.peso/100;projection['valor_projetado']=value*projection.pontuacao/100;st.dataframe(projection)
            st.caption('Valor do 18º TA informado no prompt. Projeção analítica; lacunas impedem apuração definitiva. Pontuação ausente não vira zero.')
        else:st.info('Valor mensal não informado para esta competência. Não se aplica retroativamente o valor do 18º TA.')
    elif page in ('production','quality','monitoring'):
        group={'production':'quantitativo','quality':'qualitativo','monitoring':'monitoramento'}[page];subset=t[t.grupo==group]
        st.subheader({'production':'Produção','quality':'Qualidade — PONTUAÇÃO MENSAL','monitoring':'Monitoramento sem valoração financeira direta'}[page]);st.dataframe(subset,width='stretch')
        if page=='production':
            melted=subset.melt(id_vars=['indicador'],value_vars=['meta','realizado'],var_name='série',value_name='produção');melted['produção']=pd.to_numeric(melted['produção'])
            st.plotly_chart(px.bar(melted,x='indicador',y='produção',color='série',barmode='group'),width='stretch')
            st.plotly_chart(px.bar(subset,x='indicador',y='atingimento'),width='stretch')
            chosen=st.selectbox('Indicador para tendência',subset.indicador)
            field=next(i['campo'] for i in load('indicators.yaml')['indicators'] if i['indicator_id']==chosen)
            trend=p[p.competencia.str.startswith(year)][['competencia',field]].copy();trend['acumulado']=trend[field].cumsum();st.plotly_chart(px.line(trend,x='competencia',y=[field,'acumulado'],markers=True),width='stretch')
            tri=[]
            for period in sorted({pd.Period(m,freq='Q') for m in p.competencia if m.startswith(year)}):
                tab,_=quarter(p,q,period);r=tab[tab.indicador==chosen].iloc[0];tri.append({'trimestre':str(period),'atingimento':r.atingimento})
            st.plotly_chart(px.line(pd.DataFrame(tri),x='trimestre',y='atingimento',markers=True),width='stretch')
            st.caption('Meta física: 100%. Faixa financeira máxima: a partir de 85%. Produção cirúrgica total de 688/mês é referência do prompt, sem soma automática para valoração.')
        elif page=='quality':
            st.plotly_chart(px.bar(subset,x='indicador',y='pontuacao'),width='stretch')
            for row in subset.to_dict('records'):
                st.metric(row['nome'],str(row['realizado']),delta=row['situacao'],delta_color='off')
        else:
            st.warning('Revisão de prontuários vermelho/amarelo: peso pendente de validação documental; não integra os 10 p.p.')
            st.caption('Ocupação por clínica: dados e metas por clínica não fornecidos; não inferidos.')
            for field in ['sadt_envio_data','sad_envio_data']:
                record=p[p.competencia==month]
                delivery=None if record.empty else record.iloc[0].get(field)
                deadline=pd.Timestamp(month)+pd.offsets.MonthBegin(1)+pd.Timedelta(days=24)
                st.write(f"{field}: {delivery} · Prazo: {deadline.date()} · "+('SEM DADOS' if delivery is None or pd.isna(delivery) else ('NO PRAZO' if pd.Timestamp(delivery)<=deadline else 'ATRASADO')))
        foundation(subset,month)
    elif page=='quarter':
        options=sorted({str(pd.Period(m,freq='Q')) for m in set(p.competencia)|set(q.competencia)})
        selected=st.selectbox('Trimestre',options,index=len(options)-1);period=pd.Period(selected,freq='Q');tab,tables=quarter(p,q,period)
        st.subheader('Consolidação Trimestral');st.dataframe(tab,width='stretch')
        st.plotly_chart(px.bar(tab,x='indicador',y='atingimento'),width='stretch')
        for warning in tab[tab.atingimento<85].to_dict('records'):st.warning(warning['indicador']+': '+warning['situacao'])
        st.subheader('PONTUAÇÃO MENSAL — Qualitativos')
        monthly_points=[{'competencia':str(m),'pontuacao':total(tb,'qualitativo')} for m,tb in zip(pd.period_range(period.start_time,period.end_time,freq='M'),tables)]
        st.dataframe(pd.DataFrame(monthly_points))
        points=[x['pontuacao'] for x in monthly_points]
        st.write('PROJEÇÃO TRIMESTRAL: '+('NÃO AFERÍVEL' if any(x is None for x in points) else f'{sum(points)/3:.2f} p.p. — média analítica, sem confirmação documental da consolidação financeira.'))
        qpoints=None if tab.pontuacao.isna().any() else tab.pontuacao.sum()
        values=[engine.monthly_value(str(m)) for m in pd.period_range(period.start_time,period.end_time,freq='M')]
        if all(v is not None for v in values) and qpoints is not None and all(x is not None for x in points):
            max_variable=sum(values)*.3;projected=sum(values)*qpoints/100+sum(v*x/100 for v,x in zip(values,points));st.write('PROJEÇÃO FINANCEIRA: '+currency(projected));st.write('Diferença potencial em relação ao máximo: '+currency(max_variable-projected))
        else:st.info('Projeção financeira trimestral indisponível: valores ou pontuações ausentes.')
    elif page=='governance':
        st.subheader('Governança Contratual');docs=inventory();order=[]
        for d in docs:
            rank=0 if d['document_id']=='CG018' else 8.5 if d['document_id']=='RERR08' else d['numero'];order.append(dict(d,ordem=rank))
        timeline=pd.DataFrame(sorted(order,key=lambda x:x['ordem']))
        st.plotly_chart(px.scatter(timeline,x='ordem',y='tipo_documento',color='status',hover_data=['document_id','objeto']),width='stretch')
        st.dataframe(timeline.drop(columns='ordem'),width='stretch')
        st.error('Lacunas documentais: 10º Termo Aditivo — DOCUMENTO NÃO DISPONÍVEL. Todos os demais documentos citados não foram fornecidos para auditoria.')
        st.write('8º TA → Rerratificação do 8º TA → Anexos Técnicos rerratificados. Relação declarada no prompt; originais não utilizados no cenário demonstrativo.')
        st.write('Duplicidades verificadas por hash:',duplicates(docs));st.caption('Nenhum arquivo examinado: não é possível afirmar ausência de duplicidades ou de documentos de outra unidade.')
        st.write('Documentos disponíveis: 0. Documentos excluídos após exame: 0. Históricos validados: 0.')
        st.dataframe(pd.DataFrame(load('contract_documents.yaml')['contract_financial_periods']))
        st.dataframe(pd.DataFrame(engine.rules).astype(str),width='stretch')
        st.info('Regra mais recente indicada pelo prompt: rerratificação do 8º TA. Sem corpus, não se afirma que seja a regra mais recente identificada por auditoria.')
    elif page=='data':
        st.subheader('Gestão de Dados');st.write(st.session_state.data_stats);st.dataframe(st.session_state.reports,width='stretch')
        kind=st.selectbox('Conjunto de destino',['producao','qualidade']);encoding=st.selectbox('Codificação',['utf-8','latin-1','cp1252'])
        upload=st.file_uploader('CSV, XLSX, DBF ou Parquet — somente dados agregados sintéticos',type=['csv','xlsx','dbf','parquet'])
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
                st.write('VALIDAÇÃO',stats);st.dataframe(report);st.write('PRÉVIA — linhas válidas');st.dataframe(clean.head(50))
                if stats['linhas_rejeitadas'] or (report.nivel=='ERRO').any():st.error('Arquivo inválido. Corrija todos os erros antes da consolidação.')
                elif not clean.empty:
                    confirmation=st.checkbox('Confirmo o conjunto, o mapeamento e a substituição explícita das competências coincidentes.')
                    if st.button('Confirmar consolidação',disabled=not confirmation):
                        key='production' if kind=='producao' else 'quality';current=st.session_state[key]
                        merged=pd.concat([current[~current.competencia.isin(clean.competencia)],clean],ignore_index=True).sort_values('competencia')
                        st.session_state[key]=merged
                        st.session_state.import_audit.append({'arquivo':upload.name,'mapeamento':metadata,'linhas':len(clean),'data':pd.Timestamp.now().isoformat(),'usuario':st.session_state.username})
                        st.session_state.reports=pd.concat([st.session_state.reports,report.assign(base=kind)],ignore_index=True);st.success('Consolidado na sessão. Exporte para preservar os resultados.');st.rerun()
            except Exception as exc:st.error('Falha na leitura/validação: '+str(exc))
        st.subheader('Justificativas de demanda — sem dispensa automática')
        indicator=st.selectbox('Indicador',t.indicador);status=st.selectbox('Status',DEMAND_STATUSES);note=st.text_area('Justificativa agregada, sem dados pessoais')
        if st.button('Registrar justificativa'):
            st.session_state.setdefault('justifications',[]).append({'competencia':month,'indicador':indicator,'status':status,'justificativa':note,'usuario':st.session_state.username});st.success('Registro de sessão salvo. Pontuação preservada; validação depende da Contratante.')
        st.dataframe(pd.DataFrame(st.session_state.get('justifications',[])))
        st.write('Auditoria de importações');st.json(st.session_state.import_audit)
        st.caption('Configurações não sensíveis: filtros, mapeamento e registros de justificativa na sessão. Alterações contratuais exigem revisão dos YAML, escopo e testes no Git; não há edição automática de regras pendentes.')
    st.subheader('Exportar resultados')
    tab,_=quarter(p,q,pd.Period(month,freq='Q'))
    tables={'Resumo':t,'Produção':p,'Qualidade':q,'Trimestre':tab,'Monitoramento':t[t.grupo=='monitoramento'],'Qualidade dos Dados':st.session_state.reports,'Regras Contratuais':pd.DataFrame(engine.rules).astype(str)}
    st.download_button('Baixar XLSX',workbook(tables),file_name='hdh_metas.xlsx',mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    st.download_button('Baixar CSV do resultado',csv_bytes(t),file_name='hdh_resultado.csv',mime='text/csv')
