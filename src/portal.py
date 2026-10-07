"""Four protected areas sharing public documentary data and versioned targets."""
from html import escape
import pandas as pd
import plotly.express as px
import streamlit as st
from src.auth import require_login
from src.theme import apply_theme,header,footer,sidebar_notice
from src.contract_registry import ROOT,load,inventory,duplicates
from src.contract_engine import ContractEngine
from src.historical import real_data,aggregate,evidence
from src.exports import csv_bytes,workbook
from src.formatting import currency

COLORS={'Atingida':'#24956a','Não atingida':'#d29520','Crítico':'#d35a64','SEM DADOS':'#93a3b4'}

def chart(fig):
    fig.update_layout(font=dict(family='sans-serif',color='#18364e'),paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='#ffffff',margin=dict(l=15,r=15,t=35,b=15),legend_title_text='',hovermode='x unified')
    st.plotly_chart(fig,width='stretch')

def public_documents():
    return [d for d in inventory() if d['document_id']!='DOC002']

def document_label(d):
    if d['tipo_documento']=='Parecer CMA':return 'Parecer CMA · '+str(d['periodo_avaliado'])
    number=f" {d['numero']}º" if d.get('numero') else ''
    title=d['tipo_documento']+number
    if d['tipo_documento']=='Contrato de Gestão':title+=' nº '+str(d['contrato'])
    if d.get('data_assinatura'):title+=' · '+pd.Timestamp(d['data_assinatura']).strftime('%d/%m/%Y')
    return title

def source_name(identifier):
    return next((document_label(d) for d in public_documents() if d['document_id']==identifier),str(identifier))

def present_table(frame,columns=None):
    labels={'competencia':'Competência','nome':'Indicador','indicator_id':'Código','indicador':'Código','meta':'Meta','meta_contratual':'Meta contratual','meta_reported':'Meta no parecer','realizado':'Realizado','atingimento':'Alcance (%)','pontuacao':'Pontuação (p.p.)','diferenca':'Diferença','situacao':'Situação','contrato':'Contrato','periodo':'Período','meta_acumulada':'Meta acumulada','meses_presentes':'Meses disponíveis','cobertura':'Cobertura','documentos':'Fontes','valor':'Resultado','resultado_texto':'Resultado informado','meta_aplicada':'Meta aplicada','status_dado':'Situação dos dados','observacao':'Observações','documento_fonte':'Documento','pagina_fonte':'Página','instrumento_meta':'Instrumento da meta','peso':'Peso (p.p.)','inicio_vigencia':'Início','fim_vigencia':'Fim','unidade':'Unidade','secao_fonte':'Seção','tipo_alteracao':'Alteração','status_validacao':'Validação','tipo_documento':'Tipo','numero':'Número','objeto':'Objeto','escopo_alteracao':'Alteração','status':'Situação','observacoes':'Observações','periodo_avaliado':'Período avaliado','valor_mensal':'Valor mensal (R$)','inicio':'Início','fim':'Fim','data_assinatura':'Assinatura'}
    table=frame.copy()
    if 'situacao' in table:table['situacao']=table.situacao.replace({'CRÍTICO':'Crítico','META ATINGIDA':'Atingida','ATENÇÃO':'Não atingida','META NÃO ATINGIDA':'Não atingida'})
    if columns is None:columns=[c for c in table.columns if c in labels]
    table=table[[c for c in columns if c in table]].copy()
    docs={d['document_id']:document_label(d) for d in public_documents()}
    for c in ['documento_fonte','instrumento_meta']:
        if c in table:table[c]=table[c].map(lambda v:docs.get(v,v))
    for c in ['inicio','fim','inicio_vigencia','fim_vigencia','data_assinatura']:
        if c in table:table[c]=table[c].map(lambda v:pd.Timestamp(v).strftime('%d/%m/%Y') if v and pd.notna(v) else '')
    for c in table.select_dtypes(include=['object']).columns:
        table[c]=table[c].map(lambda v:'' if pd.isna(v) else str(v))
    table=table.rename(columns=labels)
    st.dataframe(table,hide_index=True,width='stretch')

def document_view(d,key='library',show_notes=True):
    st.subheader(document_label(d));st.write(d['objeto'])
    if d.get('contrato'):st.caption('Contrato: '+d['contrato'])
    if show_notes and d.get('observacoes'):st.warning(d['observacoes'])
    if d.get('arquivo_biblioteca'):
        path=ROOT/d['arquivo_biblioteca']
        if path.is_file():
            content=path.read_bytes()
            st.download_button('Baixar documento PDF',content,file_name=d['nome_arquivo'],mime='application/pdf',key=key+'_pdf_'+d['document_id'])
            if key=='cma' and d['tipo_documento']=='Parecer CMA':
                from src.pdf_viewer import show_pdf
                show_pdf(content,key+'_'+d['document_id'])
        else:st.info('Documento temporariamente indisponível para download.')
    else:st.info('Documento não disponível na biblioteca.')

def foundation(indicator,comp,key='indicator'):
    with st.expander('Fundamentação contratual · '+indicator):
        history=ContractEngine().history(indicator)
        if not history:st.info('Definição histórica constante do parecer. Instrumento instituidor não disponível no corpus.');return
        present_table(pd.DataFrame(history),['valor','unidade','peso','inicio_vigencia','fim_vigencia','documento_fonte','pagina_fonte','tipo_alteracao'])
        if comp=='2024-07':st.warning('Transição intramensal TA08 → RERR08. Metas quantitativas iguais; não se presume eficácia retroativa da rerratificação.')
        st.info('Regra mais recente identificada no corpus disponível. 10º TA ausente: necessita validação documental da cadeia contratual.')

def filters(p,prefix):
    c1,c2=st.columns(2)
    contracts=['Todos']+sorted(p.contrato.unique())
    contract=c1.selectbox('Contrato',contracts,index=contracts.index('018/2022'),key=prefix+'_contract')
    work=p if contract=='Todos' else p[p.contrato==contract]
    years=['Todos']+sorted(work.competencia.str[:4].unique(),reverse=True)
    year=c2.selectbox('Ano',years,index=0,key=prefix+'_year')
    if year!='Todos':work=work[work.competencia.str.startswith(year)]
    return work,contract,year

def exports(p,q,key):
    with st.expander('Exportar dados e regras'):
        tabs={'Resumo':p[['competencia','indicator_id','meta_contratual','realizado','atingimento','situacao']],'Produção':p,'Qualidade':q,'Trimestre':aggregate(p),'Monitoramento':q[q.indicator_id.str.startswith('M')],'Qualidade dos Dados':pd.concat([p[p.realizado.isna()|p.divergencia_meta],q[q.status_dado!='INFORMADO']],ignore_index=True),'Regras Contratuais':pd.DataFrame(ContractEngine().rules).astype(str)}
        st.download_button('Baixar relatório XLSX',workbook(tabs),'hdh_documental.xlsx',key=key+'_xlsx')
        st.download_button('Baixar série de produção CSV',csv_bytes(p),'hdh_producao_documental.csv',key=key+'_csv')


def home(p,q):
    info=load('institutional.yaml')
    st.markdown('<div class="hdh-hero"><div class="hdh-kicker">HDH Metas · Hospital Metropolitano Sul</div><h1>Cuidar também é acompanhar.</h1><p>Conheça o hospital, acompanhe suas metas e explore a história dos resultados. Informação assistencial, instrumentos de gestão e avaliação reunidos em um mesmo espaço.</p><span class="hdh-pill">Dados documentais</span><span class="hdh-pill">Gestão do SUS</span><span class="hdh-pill">Transparência</span></div>',unsafe_allow_html=True)
    cards=st.columns(2)
    cards[0].metric('Último Parecer CMA','1º tri/2026');cards[1].metric('Vigência do termo aditivo','Jun/2028')
    left,right=st.columns([1.6,1],gap='large')
    with left:
        st.subheader('Assistência pública na Mata Sul')
        st.write('Inaugurado em 1º de julho de 2010, o Dom Helder Câmara integra a rede hospitalar pública metropolitana de Pernambuco. Localizado no Cabo de Santo Agostinho, oferece atendimento pelo SUS, com urgência e emergência em funcionamento contínuo.')
        st.write('**Especialidades assistenciais**');st.write(' · '.join(info['especialidades']))
        with st.expander('Missão, visão e valores',expanded=True):
            for k in ['missao','visao','valores']:st.write('**'+{'missao':'Missão','visao':'Visão','valores':'Valores'}[k]+'**');st.write(info[k])
    with right:
        with st.container(border=True):
            st.subheader('O hospital');st.write(info['municipio']);st.write(info['endereco']);st.write('**'+info['atendimento']+'**');st.write('Contato: '+' / '.join(info['telefones']));st.caption('CNPJ: '+info['cnpj']+' · CNES: '+info['cnes'])
        with st.container(border=True):
            st.write('**Contrato de Gestão nº 018/2022**');st.write('18º TA: 01/07/2026 a 30/06/2028.');st.write('Valor mensal expresso: '+currency(next(f['valor_mensal'] for f in load('contract_documents.yaml')['contract_financial_periods'] if f['documento_fonte']=='DOC025')));st.caption('Referência financeira futura em relação aos pareceres, que terminam em março/2026. Sem aplicação retroativa.')
    st.subheader('Explore o painel')
    c=st.columns(4)
    for col,title,text in zip(c,['Indicadores','Instrumentos de gestão','Pareceres CMA','Produção Hospitalar'],['Metas, séries mensais e regras aplicadas em cada período.','Documentos, alterações de escopo e versões das metas pactuadas.','Pareceres, histórico assistencial e acompanhamento por mês e ano.','Registros SIH/SUS do CNES 6559379: AIHs, valores, permanência, óbitos e mortalidade.']):
        with col,st.container(border=True):st.write('**'+title+'**');st.write(text)
    with st.expander('Fontes institucionais e informações de contato'):
        for source in info['fontes']:
            st.markdown(f"**[{source['nome']}]({source['url']})**")
            st.write(source['endereco'])
            if source.get('telefone'):st.write('Telefone geral: '+source['telefone'])
            if source.get('email'):st.write('E-mail do Gabinete: '+source['email'])
            if source.get('ouvidoria_telefones'):st.write('Ouvidoria: '+source['ouvidoria_telefones']+' · '+source['ouvidoria_email'])
            if source.get('email_privacidade'):st.write('Privacidade / LGPD: '+source['email_privacidade'])



def production_view(p,prefix='prod'):
    work,contract,year=filters(p,prefix)
    choices=sorted(work.indicator_id.unique());lookup=work.drop_duplicates('indicator_id').set_index('indicator_id').nome.to_dict()
    chosen=st.selectbox('Indicador assistencial',choices,format_func=lambda x:f'{x} · {lookup[x]}',key=prefix+'_indicator');series=work[work.indicator_id==chosen].sort_values('competencia').copy()
    series['situacao']=series.situacao.replace({'CRÍTICO':'Crítico','META ATINGIDA':'Atingida','ATENÇÃO':'Não atingida'})
    selected=st.selectbox('Competência',list(series.competencia),index=len(series)-1,key=prefix+'_month');row=series[series.competencia==selected].iloc[0]
    c=st.columns(4)
    for col,label,value in zip(c,['Meta contratual / referência histórica','Realizado','Alcance da meta pactuada','Pontuação financeira'],[f"{row.meta_contratual:,.0f}".replace(',','.'),'SEM DADOS' if pd.isna(row.realizado) else f"{row.realizado:,.0f}".replace(',','.'),'SEM DADOS' if pd.isna(row.atingimento) else f'{row.atingimento:.2f}%','NÃO AFERÍVEL' if pd.isna(row.pontuacao) else f'{row.pontuacao:.2f} p.p.']):col.metric(label,value)
    st.write('**'+row.situacao+'** · Instrumento da meta: '+source_name(row.instrumento_meta)+(' · p. '+str(int(row.pagina_meta)) if not pd.isna(row.pagina_meta) else ''))
    st.caption(f"Fonte do realizado: {source_name(row.documento_fonte)}, página {row.pagina_fonte}. Meta informada no parecer: {row.meta_reported:.0f}. Déficit/excedente: {'sem dados' if pd.isna(row.diferenca) else f'{row.diferenca:+.0f}' }.")
    if row.divergencia_meta:st.warning('Divergência documental: a meta informada no parecer difere da meta no anexo contratual. Cálculo do alcance usa o anexo; fonte original preservada.')
    if row.observacao and not pd.isna(row.observacao):st.info(row.observacao)
    chart(px.line(series,x='competencia',y=['realizado','meta_contratual'],markers=True,color_discrete_sequence=['#1675b8','#6c9bad'],labels={'value':'Quantidade','competencia':'Competência'},title='Produção mensal e meta do período'))
    chart(px.bar(series,x='competencia',y='atingimento',color='situacao',color_discrete_map=COLORS,labels={'atingimento':'Alcance (%)'},title='Alcance de meta pactuada'))
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
    annual=aggregate(series,'Y');chart(px.bar(annual,x='periodo',y=['realizado','meta_acumulada'],barmode='group',facet_col='contrato',title='Produção e meta acumulada no ano'));present_table(annual)


def quality_view(q,prefix='quality'):
    work,contract,year=filters(q,prefix)
    ids=sorted(work.indicator_id.unique());lookup=work.drop_duplicates('indicator_id').set_index('indicator_id').nome.to_dict()
    chosen=st.selectbox('Indicador de qualidade / monitoramento',ids,format_func=lambda x:lookup[x],key=prefix+'_indicator');series=work[work.indicator_id==chosen].sort_values('competencia')
    st.info('Resultados qualitativos mensais transcritos dos pareceres. Não reconstruímos numeradores ou denominadores ausentes. Pontuação total não é aferível quando faltam evidências.')
    cards=st.columns(3)
    cards[0].metric('Meses documentados',len(series))
    cards[1].metric('Meses sem dados',int((series.status_dado=='SEM DADOS').sum()))
    cards[2].metric('Inconsistências na fonte',int((series.status_dado=='INCONSISTÊNCIA NA FONTE').sum()))
    if series.valor.notna().any():
        chart(px.line(series,x='competencia',y='valor',markers=True,title='Resultado mensal publicado',labels={'valor':'Valor informado','competencia':'Competência'},hover_data=['resultado_texto','status_dado']))
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


def rules_view():
    rules=ContractEngine().rules;docs={d['document_id']:d for d in inventory()};sets=['CG018_ORIGINAL','TA08','RERR08','H006_CMA'];chosen=st.selectbox('Versão das metas',sets,format_func=lambda x:{'CG018_ORIGINAL':'Contrato original 018/2022','TA08':'8º Termo Aditivo — anexos históricos substituídos','RERR08':'Rerratificação do 8º TA — mais recente identificada','H006_CMA':'Contrato 006/2010 — referência secundária CMA'}[x],index=2)
    selected=[r for r in rules if r['ruleset']==chosen]
    present_table(pd.DataFrame(selected),['indicator_id','nome','valor','unidade','peso','inicio_vigencia','fim_vigencia','documento_fonte','pagina_fonte'])
    if chosen=='H006_CMA':st.warning('O contrato anterior não foi fornecido. Metas referidas nos pareceres; não se afirma o instrumento instituidor original.')
    else:st.success('Pesos da versão: 20 p.p. quantitativos + 10 p.p. qualitativos = 30 p.p.')
    st.warning('10º Termo Aditivo — DOCUMENTO NÃO DISPONÍVEL. Não se presume que deixou de alterar metas.')


def instruments():
    docs=public_documents();items=[d for d in docs if d['tipo_documento']!='Parecer CMA' and not d['excluido']]
    items.sort(key=lambda d:(d.get('data_assinatura') or '9999-12-31',d.get('numero') or 0,d['document_id']))
    st.title('Instrumentos de gestão');st.write('Do instrumento à meta: conheça o que foi pactuado e o escopo de cada alteração.')
    a,b,c=st.tabs(['Biblioteca e linha do tempo','Metas por instrumento','Auditoria e condições financeiras'])
    with a:
        timeline=pd.DataFrame([d for d in items if d['data_assinatura']]);timeline['data']=pd.to_datetime(timeline.data_assinatura)
        chart(px.scatter(timeline,x='data',y='tipo_documento',color='tipo_documento',hover_name='objeto',hover_data=['numero','objeto','escopo_alteracao'],title='Linha do tempo — datas de assinatura'))
        st.caption('8º TA → Rerratificação do 8º TA → Anexos rerratificados. Apostilamentos e aditivos possuem escopos próprios.')
        byid={d['document_id']:d for d in items};chosen=st.selectbox('Escolha o documento',list(byid),format_func=lambda x:document_label(byid[x]));document_view(byid[chosen],'instrument')
    with b:
        rules_view();st.subheader('Mapa de alterações')
        present_table(pd.DataFrame(items),['tipo_documento','numero','data_assinatura','objeto','escopo_alteracao','status'])
        chosen=st.selectbox('Instrumento para consultar metas instituídas',list(byid),format_func=lambda x:document_label(byid[x]),key='rules_instrument')
        matches=[r for r in ContractEngine().rules if r['documento_fonte']==chosen]
        if matches:present_table(pd.DataFrame(matches),['indicator_id','nome','valor','unidade','peso','documento_fonte','pagina_fonte'])
        else:st.info('Não há meta assistencial expressamente cadastrada neste instrumento. Consulte o escopo e o PDF; alterações de custeio, investimento ou prazo não revogam automaticamente metas.')
    with c:
        st.subheader('Lacunas e inconsistências')
        for text in ['10º TA indisponível; 1º TA não fornecido.','Arquivos intitulados rerratificação do 5º TA pertencem à UPA Igarassu; rerratificação HDH correspondente não localizada.','Parecer nomeado 4º tri/2023 pertence à UPA Imbiribeira. Histórico 2023 obtido do parecer anual do HDH.','Parecer nomeado 4º tri/2022 é cópia do 3º trimestre; 4º trimestre obtido do anual.','Parecer nomeado 4º tri/2020 identifica internamente 4º tri/2019.','Revisão de prontuários vermelho/amarelo no anexo rerratificado não possui peso próprio na súmula.']:st.warning(text)
        present_table(pd.DataFrame(docs),['tipo_documento','numero','periodo_avaliado','contrato','status','observacoes'])
        st.download_button('Exportar inventário CSV',csv_bytes(pd.DataFrame(docs)),'inventario_documental.csv')
        st.subheader('Condições Financeiras do Contrato')
        st.write('16º TA, p.1: parcela de 70% até o quinto dia útil; 30% até o dia 30, condicionada à validação do envio de prestação de contas.');st.caption('Esta condição de pagamento é distinta da avaliação: 20% quantitativos + 10% qualitativos.')
        present_table(pd.DataFrame(load('contract_documents.yaml')['contract_financial_periods']))
        st.info('Valores anteriores preservados como referências expressas, com lacunas de composição e vigência. Projeção automática limitada ao período explicitamente delimitado pelo 18º TA.')


def cma_sources(document,p):
    import re
    text=evidence(document['duplicate_of'] or document['document_id'])
    mentioned=[]
    if 'SIMAS' in text:mentioned.append('Sistema de Monitoramento de Metas Assistenciais (SIMAS)')
    reports=sorted(set(re.findall(r'CTAI\s+n[º°o.]?\s*(\d+/\d{4})',text,re.I)))
    if reports:mentioned.append('Pareceres técnicos CTAI: '+', '.join(reports))
    elif 'CTAI' in text:mentioned.append('Pareceres técnicos da Comissão Técnica de Acompanhamento Interno (CTAI)')
    if mentioned:
        st.write('**Fontes mencionadas no parecer**')
        for source in mentioned:st.write('• '+source)
    period=document['periodo_avaliado']
    if not period:return
    mask=p.competencia.str.startswith(period) if len(period)==4 else pd.PeriodIndex(p.competencia,freq='M').asfreq('Q').astype(str)==period
    rows=p[mask]
    if not rows.empty:
        st.write('**Metas e fontes usadas no painel para este período**')
        present_table(rows[['nome','meta_contratual','instrumento_meta','pagina_meta','documento_fonte','pagina_fonte']].drop_duplicates(),['nome','meta_contratual','instrumento_meta','documento_fonte','pagina_fonte'])
        st.caption('Quando o parecer trimestral não é a fonte canônica, os meses são transcritos do anual correspondente, evitando dupla contagem. As metas seguem o instrumento contratual identificado.')

def cma(p,q):
    st.title('Comissão Mista de Avaliação');st.write('Pareceres, evidências e séries históricas para acompanhar resultados ao longo do tempo.')
    a,c,d=st.tabs(['Pareceres','Comparação anual','Qualidade e evidências'])
    with a:
        items=[d for d in public_documents() if d['tipo_documento']=='Parecer CMA' and not d['excluido']]
        years=['Todos']+sorted({d['periodo_avaliado'][:4] for d in items},reverse=True);year=st.selectbox('Ano do parecer',years)
        selected=[d for d in items if year=='Todos' or d['periodo_avaliado'].startswith(year)]
        selected.sort(key=lambda x:(x['periodo_avaliado'],x['document_id']),reverse=True)
        byid={d['document_id']:d for d in selected};chosen=st.selectbox('Parecer disponível',list(byid),format_func=lambda x:document_label(byid[x]));document_view(byid[chosen],'cma',show_notes=False)
        cma_sources(byid[chosen],p)
        st.caption('Pareceres são documentos de avaliação. Sua meta informada não altera, por si só, o instrumento contratual. Séries canônicas usam pareceres anuais para evitar dupla contagem; 2026 usa o parecer do 1º trimestre.')
        present_table(pd.DataFrame(selected),['periodo_avaliado','contrato','status'])
    with c:
        data=aggregate(p,'Y');ids=sorted(data.indicator_id.unique());chosen=st.selectbox('Indicador na comparação anual',ids,key='cma_annual_indicator');data=data[data.indicator_id==chosen]
        chart(px.bar(data,x='periodo',y=['realizado','meta_acumulada'],barmode='group',facet_col='contrato',title='Comparação anual por contrato'));present_table(data)
        st.caption('2022 possui dois contratos; 2026 contém janeiro a março. Ausência ou análise impossibilitada não equivale a zero. Não comparar consultas de escopos diferentes como uma única série.')
    with d:
        quality_view(q,'cma_quality');st.subheader('Qualidade documental dos dados')
        present_table(p[p.realizado.isna()|p.divergencia_meta]);present_table(q[q.status_dado!='INFORMADO'])
    exports(p,q,'cma')


def indicators_page(p,q):
    st.title('Indicadores');st.write('Metas, produção e qualidade com referência à regra de cada período.')
    tabs=st.tabs(['Produção assistencial','Qualidade e monitoramento','Metas e projeções']+(['Gestão de dados'] if st.session_state.get('role')=='ADMIN' else []))
    a,b,c=tabs[:3]
    with a:production_view(p)
    with b:quality_view(q)
    with c:
        rules_view();st.subheader('PROJEÇÃO FINANCEIRA')
        st.info('Os dados reais disponíveis terminam em março/2026. O valor mensal do 18º TA só se aplica a partir de julho/2026; não é usado retroativamente.')
        st.caption('Projeção exige pontuação completa, valor aplicável e validação das evidências. Não representa valor definitivo a pagar.')
    if len(tabs)>3:
        with tabs[3]:
            from src.data_ui import render_data
            render_data()
    exports(p,q,'indicators')


def render(page):
    require_login(show_logout=False);apply_theme();header()
    p,q=real_data()
    sidebar_notice()
    if page=='home':home(p,q)
    elif page=='indicators':indicators_page(p,q)
    elif page=='instruments':instruments()
    elif page=='cma':cma(p,q)
    footer()
