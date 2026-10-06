import os,time,hmac
import bcrypt
import streamlit as st
def credentials():
    try: auth=dict(st.secrets.get('auth',{}))
    except Exception: auth={}
    username=os.getenv('ADMIN_USERNAME') or auth.get('admin_username')
    hashed=os.getenv('ADMIN_PASSWORD_HASH') or auth.get('admin_password_hash')
    try:
        if not username or not hashed: return None
        bcrypt.checkpw(b'configuration-check',hashed.encode())
    except (ValueError,TypeError):return None
    return username,hashed
def verify(username,password,expected,hashed):
    try:return hmac.compare_digest(username,expected) and bcrypt.checkpw(password.encode(),hashed.encode())
    except (ValueError,TypeError):return False
def logout():
    st.session_state.clear()
    st.rerun()
def require_login():
    if st.session_state.get('authenticated'):
        if time.time()-st.session_state.get('login_time',0)>3600:logout()
        if st.sidebar.button('Sair'):logout()
        return
    st.title('HDH Metas · Login')
    st.caption('Protótipo demonstrativo para estudo de caso profissional.')
    conf=credentials()
    if conf is None:
        st.error('Configuração incompleta. Configure ADMIN_USERNAME e ADMIN_PASSWORD_HASH. Consulte o README.');st.stop()
    blocked=st.session_state.get('blocked_until',0)
    if time.time()<blocked:
        st.warning('Tentativas excedidas. Aguarde 30 segundos e atualize a página.');st.stop()
    with st.form('login',clear_on_submit=True):
        user=st.text_input('Usuário');password=st.text_input('Senha',type='password');submit=st.form_submit_button('Entrar')
    if submit:
        if verify(user,password,*conf):
            st.session_state.update(authenticated=True,username=user,role='ADMIN',login_time=time.time());st.session_state.pop('failures',None);st.rerun()
        else:
            failures=st.session_state.get('failures',0)+1;st.session_state['failures']=failures
            if failures>=5:st.session_state.update(blocked_until=time.time()+30,failures=0)
            st.error('Credenciais inválidas.')
    st.stop()
