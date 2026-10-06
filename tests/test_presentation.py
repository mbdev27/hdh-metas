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
