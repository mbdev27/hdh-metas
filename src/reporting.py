"""Cached exports of public documentary data; session uploads remain uncached."""
import pandas as pd
import streamlit as st
from src.historical import aggregate
from src.contract_engine import ContractEngine
from src.exports import workbook


@st.cache_data(max_entries=4,show_spinner=False)
def documentary_workbook(p,q,rule_version):
    tables={'Resumo':p[['competencia','indicator_id','meta_contratual','realizado','atingimento','situacao']],
            'Produção':p,'Qualidade':q,'Trimestre':aggregate(p),
            'Monitoramento':q[q.indicator_id.str.startswith('M')],
            'Qualidade dos Dados':pd.concat([p[p.realizado.isna()|p.divergencia_meta],q[q.status_dado!='INFORMADO']],ignore_index=True),
            'Regras Contratuais':pd.DataFrame(ContractEngine().rules).astype(str)}
    return workbook(tables)


@st.cache_data(max_entries=4,show_spinner=False)
def sih_workbook(data,selected,metadata):
    return workbook({'Mensal':selected,'Anuais publicados':data[(data.tipo_linha=='ano_publicado')&(data.ano>=2020)],
                     'Metadados':pd.DataFrame(metadata).astype(str),'Totais originais':data[data.tipo_linha=='total_publicado']})
