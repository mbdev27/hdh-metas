from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest
from src.pdf_viewer import page_count,page_image
from src.contract_registry import inventory,ROOT


def test_all_available_cma_pdfs_render_first_page():
    documents=[d for d in inventory() if d['tipo_documento']=='Parecer CMA' and not d['excluido'] and d.get('arquivo_biblioteca')]
    assert documents
    for document in documents:
        content=(ROOT/document['arquivo_biblioteca']).read_bytes()
        assert page_count(content)>0
        assert page_image(content,0).startswith(b'\x89PNG\r\n\x1a\n')


def test_pdf_page_boundaries():
    document=next(d for d in inventory() if d['tipo_documento']=='Parecer CMA' and not d['excluido'] and d.get('arquivo_biblioteca'))
    content=(ROOT/document['arquivo_biblioteca']).read_bytes()
    with pytest.raises(ValueError):page_image(content,page_count(content))
    with pytest.raises(ValueError):page_image(content,-1)


def test_bad_preview_has_friendly_fallback():
    at=AppTest.from_string("from src.pdf_viewer import show_pdf\nshow_pdf(b'not a pdf','bad')").run()
    assert not at.exception and not at.error
    assert any('Use o botão de download' in item.value for item in at.info)
