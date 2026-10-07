"""Document ui."""
from html import escape
import pandas as pd
import plotly.express as px
import streamlit as st
from src.contract_registry import ROOT, inventory
from src.contract_engine import ContractEngine
from src.cache import bytes_versioned,file_version
from src.presentation import document_label, present_table

def document_view(d,key='library',show_notes=True):
    st.subheader(document_label(d));st.write(d['objeto'])
    if d.get('contrato'):st.caption('Contrato: '+d['contrato'])
    if show_notes and d.get('observacoes'):st.warning(d['observacoes'])
    if d.get('arquivo_biblioteca'):
        path=ROOT/d['arquivo_biblioteca']
        if path.is_file():
            content=bytes_versioned(file_version(path))
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


def rules_view():
    rules=ContractEngine().rules;docs={d['document_id']:d for d in inventory()};sets=['CG018_ORIGINAL','TA08','RERR08','H006_CMA'];chosen=st.selectbox('Versão das metas',sets,format_func=lambda x:{'CG018_ORIGINAL':'Contrato original 018/2022','TA08':'8º Termo Aditivo — anexos históricos substituídos','RERR08':'Rerratificação do 8º TA — mais recente identificada','H006_CMA':'Contrato 006/2010 — referência secundária CMA'}[x],index=2)
    selected=[r for r in rules if r['ruleset']==chosen]
    present_table(pd.DataFrame(selected),['indicator_id','nome','valor','unidade','peso','inicio_vigencia','fim_vigencia','documento_fonte','pagina_fonte'])
    if chosen=='H006_CMA':st.warning('O contrato anterior não foi fornecido. Metas referidas nos pareceres; não se afirma o instrumento instituidor original.')
    else:st.success('Pesos da versão: 20 p.p. quantitativos + 10 p.p. qualitativos = 30 p.p.')
    st.warning('10º Termo Aditivo — DOCUMENTO NÃO DISPONÍVEL. Não se presume que deixou de alterar metas.')


def instrument_timeline(items):
    from textwrap import wrap
    timeline=pd.DataFrame([d for d in items if d.get('data_assinatura')])
    timeline['data']=pd.to_datetime(timeline.data_assinatura)
    timeline['instrumento']=timeline.apply(lambda row:document_label(row.to_dict()),axis=1)
    timeline['objetivo']=timeline.objeto.map(lambda text:'<br>'.join(escape(line) for line in wrap(str(text),65)))
    timeline['impacto']=timeline.escopo_alteracao.map(lambda text:escape(str(text)))
    timeline['assinatura']=timeline.data.dt.strftime('%d/%m/%Y')
    return px.scatter(timeline,x='data',y='tipo_documento',color='tipo_documento',hover_name='instrumento',
        hover_data={'data':False,'tipo_documento':False,'objetivo':True,'impacto':True,'assinatura':True},
        labels={'data':'Data de assinatura','tipo_documento':'Tipo de instrumento','objetivo':'Objetivo do instrumento','impacto':'Escopo da alteração','assinatura':'Assinatura'},
        title='Linha do tempo — datas de assinatura')


