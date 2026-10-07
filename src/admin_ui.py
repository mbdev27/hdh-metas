"""Admin-only presentation; permission is also enforced by the history reader."""
from datetime import date,datetime,timedelta,timezone
import json
import pandas as pd
import streamlit as st
from src.auth import require_login
from src.access_history import AccessHistory,EVENTS,history_path,require_admin
from src.restructuring.schema import current_actor
from src.theme import apply_theme,header,footer
from src.exports import csv_bytes
RECIFE=timezone(timedelta(hours=-3))


def render_admin():
    require_login(show_logout=False)
    actor=current_actor(st.session_state)
    try:require_admin(actor)
    except PermissionError:
        st.warning('Esta área está disponível apenas para o usuário admin.');st.stop()
    apply_theme();header();st.title('Administração')
    st.subheader('Histórico de acessos')
    st.caption('Logins confirmados, saídas pelo botão Sair e expirações detectadas ao voltar ao aplicativo. Horários de Recife (UTC−3). Nenhuma senha, IP ou dado de paciente é registrado.')
    st.caption('Fechar o navegador não gera logout confirmado. A duração indicada é o intervalo da sessão, não o tempo de uso ativo.')
    st.warning('O histórico é salvo em JSON. No Streamlit Cloud, arquivos locais podem desaparecer após reinicializações. Baixe uma cópia para preservar os registros.')
    try:rows=AccessHistory(history_path()).read(actor)
    except Exception:
        st.error('Não foi possível consultar o histórico. Verifique o armazenamento com o responsável pelo painel.');footer();return
    if not rows:st.info('Ainda não há acessos registrados. O histórico começa nesta atualização.');footer();return
    events=[{**row,'local_date':datetime.fromisoformat(row['timestamp']).astimezone(RECIFE).date()} for row in rows]
    period=st.date_input('Período dos acessos',value=(min(r['local_date'] for r in events),datetime.now(RECIFE).date()),key='access_history_period')
    if len(period)!=2:st.info('Selecione início e fim.');return
    users=st.multiselect('Usuários',sorted({r['username'] for r in rows}),default=sorted({r['username'] for r in rows}))
    event=st.selectbox('Tipo de acesso',['Todos']+list(EVENTS),format_func=lambda value:EVENTS.get(value,value))
    filtered=[r for r in events if period[0]<=r['local_date']<=period[1] and r['username'] in users and (event=='Todos' or r['event']==event)]
    cards=st.columns(3)
    cards[0].metric('Logins no período',sum(r['event']=='LOGIN' for r in filtered))
    cards[1].metric('Saídas pelo botão',sum(r['event']=='LOGOUT' for r in filtered))
    cards[2].metric('Expirações detectadas',sum(r['event']=='SESSION_EXPIRED' for r in filtered))
    frame=pd.DataFrame([{'Data e hora (Recife)':datetime.fromisoformat(r['timestamp']).astimezone(RECIFE).strftime('%d/%m/%Y %H:%M:%S'),'Usuário':r['username'],'Perfil':r['role'],'Evento':EVENTS[r['event']],'Duração da sessão (s)':r['session_seconds']} for r in filtered])
    if frame.empty:st.info('Nenhum registro para os filtros selecionados.')
    else:
        st.dataframe(frame,hide_index=True,width='stretch')
        st.download_button('Baixar recorte CSV',csv_bytes(frame),'historico_acessos.csv',mime='text/csv')
    # Full history is exported only inside this authenticated admin-only page.
    st.download_button('Baixar histórico completo JSON',json.dumps({'format_version':1,'events':rows},ensure_ascii=False,indent=2).encode('utf-8'),'historico_acessos_completo.json',mime='application/json')
    footer()
