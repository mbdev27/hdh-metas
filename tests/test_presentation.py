from streamlit.testing.v1 import AppTest
from src.portal import document_label,public_documents
from src.contract_registry import inventory

def test_legal_reference_not_in_visible_library():
    assert 'DOC002' not in {d['document_id'] for d in public_documents()}
    # Kept internally for rules/auditing, never mistaken for a missing attachment.
    assert 'DOC002' in {d['document_id'] for d in inventory()}

def test_document_label_omits_missing_dates_and_internal_ids():
    label=document_label(next(d for d in inventory() if d['document_id']=='DOC001'))
    assert label=='Organograma'
    assert 'sem data' not in label

def test_failure_has_friendly_message_not_traceback():
    app=AppTest.from_string('from src.safe_ui import run_safely\nrun_safely(lambda: 1/0)').run()
    assert not app.exception
    assert len(app.error)==1
    assert 'Não foi possível carregar esta área' in app.error[0].value
    assert 'ZeroDivisionError' not in app.error[0].value


def test_home_contacts_and_summary():
    import time
    from pathlib import Path
    at=AppTest.from_file(Path(__file__).resolve().parents[1]/'pages/01_Tela_Inicial.py',default_timeout=40)
    for key,value in dict(authenticated=True,username='admin',role='ADMIN',login_time=time.time()).items():at.session_state[key]=value
    at.run()
    assert not at.error and not at.exception
    assert [m.label for m in at.metric]==['Último Parecer CMA','Vigência do termo aditivo']
    text=' '.join(m.value for m in at.markdown)
    assert '6559379' in text and 'adm.gab.ses@saude.pe.gov.br' in text
    assert 'dpo@fgh.org.br' in text
    assert 'HDH METAS / MONITORAMENTO CONTRATUAL' not in text


def test_quality_categorical_uses_charts_without_result_table():
    at=AppTest.from_string("from src.portal import quality_view\nfrom src.historical import real_data\np,q=real_data()\nquality_view(q[q.nome=='Escala médica'],'categorical')").run()
    assert not at.exception and not at.error
    assert len(at.get('plotly_chart'))==2
    # Contractual foundation may contain a separate rule table; result series must not.
    assert not any('Resultado informado' in frame.value.columns for frame in at.dataframe)


def test_cma_pdf_preview_and_no_monthly_tab():
    import time
    from pathlib import Path
    at=AppTest.from_file(Path(__file__).resolve().parents[1]/'pages/04_Pareceres_CMA.py',default_timeout=40)
    for key,value in dict(authenticated=True,username='admin',role='ADMIN',login_time=time.time()).items():at.session_state[key]=value
    at.run()
    assert not at.error and not at.exception
    assert 'Histórico mensal' not in [tab.label for tab in at.tabs]
    assert any(exp.label=='Visualizar parecer PDF' for exp in at.expander)
    assert len(at.get('image'))>0


def test_status_labels():
    from src.portal import COLORS
    assert 'Não atingida' in COLORS
    assert 'Não alcançada' not in COLORS
