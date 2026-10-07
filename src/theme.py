import streamlit as st

def apply_theme():
    st.markdown('''<style>
    .stApp {background:#f5f8fc;color:#18364e}
    .block-container {padding-top:2rem;padding-bottom:2rem;max-width:1500px}
    [data-testid="stSidebar"] {background:#edf3fa;border-right:1px solid #dce5ef}
    h1,h2,h3 {color:#123b60;letter-spacing:-.025em}
    [data-testid="stMetric"] {background:#fff;border:1px solid #dce6f0;border-radius:14px;padding:18px;box-shadow:0 3px 12px #123b6005}
    [data-testid="stMetricLabel"] {color:#50657c}
    [data-testid="stMetricValue"] {color:#123b60;font-size:1.7rem}
    [data-testid="stForm"] {background:white;border:1px solid #d9e5f0;border-radius:18px;padding:28px}
    .hdh-hero {background:linear-gradient(125deg,#102f50,#176fa1);color:white;border-radius:22px;padding:38px;margin-bottom:22px}
    .hdh-hero h1,.hdh-hero h2,.hdh-hero h3 {color:white;margin:8px 0 18px}
    .hdh-hero p {color:#e5f3ff;font-size:1.05rem;line-height:1.65;max-width:800px}
    .hdh-kicker {font-size:.78rem;font-weight:700;letter-spacing:.13em;text-transform:uppercase;color:#aed8f7}
    .hdh-pill {display:inline-block;background:#ffffff18;border:1px solid #ffffff40;border-radius:30px;padding:5px 12px;font-size:.8rem;margin-right:6px}
    .hdh-footer {border-top:1px solid #dce5ef;padding-top:14px;color:#60748a;font-size:.78rem;margin-top:24px}
    button[kind="primary"] {border-radius:9px}
    </style>''',unsafe_allow_html=True)

def header():
    st.caption('Protótipo demonstrativo para estudo de caso profissional. Sem vínculo oficial com FGH, SES/PE ou Governo de Pernambuco.')

def footer():
    st.markdown('<div class="hdh-footer">HDH Metas · Protótipo demonstrativo para estudo de caso profissional.<br>Dados documentais públicos e agregados. Não inserir dados pessoais identificáveis de pacientes.</div>',unsafe_allow_html=True)

def sidebar_notice():
    st.sidebar.caption('Painel de apoio à gestão, inspirado em boas práticas de uso de dados em saúde e orientado pelos princípios brasileiros de Saúde Digital. Utiliza dados públicos agregados, sem dados pessoais sensíveis, com cuidados de proteção de dados e respeito à LGPD.')
