"""Page-by-page PDF preview, preserving the original layout without browser plugins."""
import logging
import streamlit as st

@st.cache_data(max_entries=32,show_spinner=False)
def page_count(content: bytes) -> int:
    import pymupdf
    with pymupdf.open(stream=content,filetype='pdf') as document:
        return len(document)

@st.cache_data(max_entries=24,show_spinner=False)
def page_image(content: bytes, page: int) -> bytes:
    import pymupdf
    with pymupdf.open(stream=content,filetype='pdf') as document:
        if not 0 <= page < len(document):raise ValueError('Invalid PDF page')
        return document[page].get_pixmap(dpi=120,alpha=False).tobytes('png')

def show_pdf(content: bytes,key: str):
    try:
        count=page_count(content)
        if not count:raise ValueError('Empty PDF')
        with st.expander('Visualizar parecer PDF',expanded=True):
            page=st.number_input('Página do parecer',min_value=1,max_value=count,value=1,step=1,key=key+'_page')
            st.caption(f'Página {page} de {count}')
            st.image(page_image(content,page-1),width='stretch')
    except Exception:
        logging.getLogger(__name__).exception('PDF preview unavailable')
        st.info('Não foi possível exibir a prévia. Use o botão de download para abrir o PDF.')
