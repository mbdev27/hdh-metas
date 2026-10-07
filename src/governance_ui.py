"""Governance ui."""
import pandas as pd
import streamlit as st
from src.contract_registry import load
from src.contract_engine import ContractEngine
from src.exports import csv_bytes
from src.presentation import chart, public_documents, document_label, present_table, section
from src.document_ui import document_view, rules_view, instrument_timeline

def instruments():
    docs=public_documents();items=[d for d in docs if d['tipo_documento']!='Parecer CMA' and not d['excluido']]
    items.sort(key=lambda d:(d.get('data_assinatura') or '9999-12-31',d.get('numero') or 0,d['document_id']))
    st.title('Instrumentos de gestão');st.write('Do instrumento à meta: conheça o que foi pactuado e o escopo de cada alteração.')
    byid={d['document_id']:d for d in items}
    active=section(['Biblioteca e linha do tempo','Metas por instrumento','Auditoria e condições financeiras'],'instrument_section')
    if active=='Biblioteca e linha do tempo':
        chart(instrument_timeline(items),hovermode='closest')
        st.caption('8º TA → Rerratificação do 8º TA → Anexos rerratificados. Apostilamentos e aditivos possuem escopos próprios.')
        byid={d['document_id']:d for d in items};chosen=st.selectbox('Escolha o documento',list(byid),format_func=lambda x:document_label(byid[x]));document_view(byid[chosen],'instrument')
    elif active=='Metas por instrumento':
        rules_view();st.subheader('Mapa de alterações')
        present_table(pd.DataFrame(items),['tipo_documento','numero','data_assinatura','objeto','escopo_alteracao','status'])
        chosen=st.selectbox('Instrumento para consultar metas instituídas',list(byid),format_func=lambda x:document_label(byid[x]),key='rules_instrument')
        matches=[r for r in ContractEngine().rules if r['documento_fonte']==chosen]
        if matches:present_table(pd.DataFrame(matches),['indicator_id','nome','valor','unidade','peso','documento_fonte','pagina_fonte'])
        else:st.info('Não há meta assistencial expressamente cadastrada neste instrumento. Consulte o escopo e o PDF; alterações de custeio, investimento ou prazo não revogam automaticamente metas.')
    elif active=='Auditoria e condições financeiras':
        st.subheader('Lacunas e inconsistências')
        for text in ['10º TA indisponível; 1º TA não fornecido.','Arquivos intitulados rerratificação do 5º TA pertencem à UPA Igarassu; rerratificação HDH correspondente não localizada.','Parecer nomeado 4º tri/2023 pertence à UPA Imbiribeira. Histórico 2023 obtido do parecer anual do HDH.','Parecer nomeado 4º tri/2022 é cópia do 3º trimestre; 4º trimestre obtido do anual.','Parecer nomeado 4º tri/2020 identifica internamente 4º tri/2019.','Revisão de prontuários vermelho/amarelo no anexo rerratificado não possui peso próprio na súmula.']:st.warning(text)
        present_table(pd.DataFrame(docs),['tipo_documento','numero','periodo_avaliado','contrato','status','observacoes'])
        st.download_button('Exportar inventário CSV',csv_bytes(pd.DataFrame(docs)),'inventario_documental.csv')
        st.subheader('Condições Financeiras do Contrato')
        st.write('16º TA, p.1: parcela de 70% até o quinto dia útil; 30% até o dia 30, condicionada à validação do envio de prestação de contas.');st.caption('Esta condição de pagamento é distinta da avaliação: 20% quantitativos + 10% qualitativos.')
        present_table(pd.DataFrame(load('contract_documents.yaml')['contract_financial_periods']))
        st.info('Valores anteriores preservados como referências expressas, com lacunas de composição e vigência. Projeção automática limitada ao período explicitamente delimitado pelo 18º TA.')


