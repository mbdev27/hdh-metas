import os,time,hmac
import bcrypt
import streamlit as st
def credentials():
    try: auth=dict(st.secrets.get('auth',{}))
    except Exception: auth={}
    username=os.getenv('ADMIN_USERNAME') or auth.get('admin_username')
    if username=='adm': username='admin'  # Migrate the original account without changing its hash.
    hashed=os.getenv('ADMIN_PASSWORD_HASH') or auth.get('admin_password_hash')
    try:
        if not username or not hashed: return None
        bcrypt.checkpw(b'configuration-check',hashed.encode())
    except (ValueError,TypeError):return None
    return username,hashed
def accounts():
    admin=credentials()
    if admin is None:return []
    configured=[(admin[0],admin[1],'ADMIN')]
    try:auth=dict(st.secrets.get('auth',{}))
    except Exception:auth={}
    name=os.getenv('DIRECTOR_USERNAME') or auth.get('director_username','diretoria')
    hashed=os.getenv('DIRECTOR_PASSWORD_HASH') or auth.get('director_password_hash')
    try:
        if hashed and name!=admin[0]:
            bcrypt.checkpw(b'configuration-check',hashed.encode())
            configured.append((name,hashed,'GESTOR'))
    except (ValueError,TypeError,AttributeError):pass
    return configured

def verify(username,password,expected,hashed):
    try:return hmac.compare_digest(username,expected) and bcrypt.checkpw(password.encode(),hashed.encode())
    except (ValueError,TypeError):return False
def logout():
    st.session_state.clear()
    st.rerun()
def require_login(show_logout=True):
    if st.session_state.get('authenticated'):
        if st.session_state.get('username')=='adm': st.session_state['username']='admin'
        if time.time()-st.session_state.get('login_time',0)>3600:logout()
        if show_logout and st.sidebar.button('Sair',key='logout'):logout()
        return
    from src.theme import apply_theme,footer
    apply_theme()
    st.markdown('<style>[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], [data-testid="collapsedControl"] {display:none !important;}</style>',unsafe_allow_html=True)
    left,right=st.columns([1.25,1],gap='large')
    with left:
        st.markdown('<div class="hdh-hero"><div class="hdh-kicker">Informação · Saúde · Gestão</div><h1>HDH Metas</h1><h3>Informação para acompanhar.<br>Clareza para decidir.</h3><p>Um espaço para acompanhar as metas do Hospital Metropolitano Sul Dom Helder Câmara, conhecer os instrumentos de gestão e consultar a trajetória dos resultados assistenciais.</p><span class="hdh-pill">Indicadores</span><span class="hdh-pill">Rastreabilidade</span><span class="hdh-pill">Séries históricas</span></div>',unsafe_allow_html=True)
        st.caption('Protótipo demonstrativo para estudo de caso profissional. Sem vínculo oficial com FGH, SES/PE ou Governo de Pernambuco.')
    with right:
        st.subheader('Bem-vindo ao HDH Metas')
        st.write('Entre com suas credenciais para acessar o painel.')
    configured=accounts()
    if not configured:
        st.error('Configuração incompleta. Configure ADMIN_USERNAME e ADMIN_PASSWORD_HASH. Consulte o README.');st.stop()
    blocked=st.session_state.get('blocked_until',0)
    if time.time()<blocked:
        st.warning('Tentativas excedidas. Aguarde 30 segundos e atualize a página.');st.stop()
    with right, st.form('login',clear_on_submit=True):
        user=st.text_input('Usuário');password=st.text_input('Senha',type='password');submit=st.form_submit_button('Acessar painel',type='primary',use_container_width=True)
    if submit:
        role=next((role for name,hashed,role in configured if verify(user,password,name,hashed)),None)
        if role:
            st.session_state.update(authenticated=True,username=user,role=role,login_time=time.time());st.session_state.pop('failures',None);st.rerun()
        else:
            failures=st.session_state.get('failures',0)+1;st.session_state['failures']=failures
            if failures>=5:st.session_state.update(blocked_until=time.time()+30,failures=0)
            st.error('Credenciais inválidas.')
    st.stop()
