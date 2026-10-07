"""Home ui."""
import streamlit as st
from src.contract_registry import load
from src.formatting import currency

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


