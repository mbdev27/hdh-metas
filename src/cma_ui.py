"""Cma ui."""
import pandas as pd
import streamlit as st
from src.historical import aggregate, evidence
from src.presentation import chart, public_documents, document_label, present_table, exports, section
from src.document_ui import document_view
from src.indicator_views import quality_view
from src.charts import annual_chart
from src.management import comparable_annual

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
    active=section(['Pareceres','Comparação anual','Qualidade e evidências'],'cma_section')
    if active=='Pareceres':
        items=[d for d in public_documents() if d['tipo_documento']=='Parecer CMA' and not d['excluido']]
        years=['Todos']+sorted({d['periodo_avaliado'][:4] for d in items},reverse=True);year=st.selectbox('Ano do parecer',years)
        selected=[d for d in items if year=='Todos' or d['periodo_avaliado'].startswith(year)]
        selected.sort(key=lambda x:(x['periodo_avaliado'],x['document_id']),reverse=True)
        byid={d['document_id']:d for d in selected};chosen=st.selectbox('Parecer disponível',list(byid),format_func=lambda x:document_label(byid[x]));document_view(byid[chosen],'cma',show_notes=False)
        cma_sources(byid[chosen],p)
        st.caption('Pareceres são documentos de avaliação. Sua meta informada não altera, por si só, o instrumento contratual. Séries canônicas usam pareceres anuais para evitar dupla contagem; 2026 usa o parecer do 1º trimestre.')
        present_table(pd.DataFrame(selected),['periodo_avaliado','contrato','status'])
    elif active=='Comparação anual':
        ids=sorted(p.indicator_id.unique());chosen=st.selectbox('Indicador na comparação anual',ids,key='cma_annual_indicator')
        same=st.checkbox('Comparar os mesmos meses entre anos',key='cma_same_months')
        data=aggregate(comparable_annual(p[p.indicator_id==chosen],same),'Y')
        chart(annual_chart(data,'Comparação anual por contrato'));present_table(data)
        st.caption('2022 possui dois contratos; 2026 contém janeiro a março. Ausência ou análise impossibilitada não equivale a zero. Não comparar consultas de escopos diferentes como uma única série.')
    elif active=='Qualidade e evidências':
        quality_view(q,'cma_quality');st.subheader('Qualidade documental dos dados')
        present_table(p[p.realizado.isna()|p.divergencia_meta]);present_table(q[q.status_dado!='INFORMADO'])
    exports(p,q,'cma')


