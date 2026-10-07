"""Presentation."""
import pandas as pd
import streamlit as st
from src.contract_registry import ROOT, inventory
from src.exports import csv_bytes
from src.cache import file_version
from src.reporting import documentary_workbook
from src.charts import COLORS  # Shared palette, also exported for screen modules.



def chart(fig,hovermode="x unified"):
    fig.update_layout(font=dict(family='sans-serif',color='#18364e'),paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='#ffffff',margin=dict(l=15,r=15,t=35,b=15),legend_title_text='',hovermode=hovermode)
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
    for c in table.select_dtypes(include=['object','str']).columns:
        table[c]=table[c].map(lambda v:'' if pd.isna(v) else str(v))
    table=table.rename(columns=labels)
    st.dataframe(table,hide_index=True,width='stretch')


def filters(p,prefix):
    c1,c2=st.columns(2)
    contracts=['Todos']+sorted(p.contrato.unique())
    contract=c1.selectbox('Contrato',contracts,index=contracts.index('018/2022') if '018/2022' in contracts else 0,key=prefix+'_contract')
    work=p if contract=='Todos' else p[p.contrato==contract]
    years=['Todos']+sorted(work.competencia.str[:4].unique(),reverse=True)
    year=c2.selectbox('Ano',years,index=0,key=prefix+'_year')
    if year!='Todos':work=work[work.competencia.str.startswith(year)]
    return work,contract,year


def exports(p,q,key):
    with st.expander('Exportar dados e regras'):
        if not st.checkbox('Preparar arquivos para download',key=key+'_prepare_exports'):
            return
        st.download_button('Baixar relatório XLSX',documentary_workbook(p,q,file_version(ROOT/'config/contract_rules.yaml')),'hdh_documental.xlsx',key=key+'_xlsx')
        st.download_button('Baixar série de produção CSV',csv_bytes(p),'hdh_producao_documental.csv',key=key+'_csv')




def section(options,key):
    """Only the selected section is executed; unlike eagerly rendered tabs."""
    default=None if key in st.session_state else options[0]
    return st.segmented_control('Seção',options,default=default,key=key) or options[0]
