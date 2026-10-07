"""Protected page routing; presentation and screens live in dedicated modules."""
from src.auth import require_login
from src.theme import apply_theme,header,footer,sidebar_notice
from src.historical import real_data
# Compatibility exports for existing integrations.
from src.presentation import chart,public_documents,document_label,source_name,present_table,COLORS
from src.document_ui import instrument_timeline
from src.indicator_views import quality_view
from src.home_ui import home
from src.governance_ui import instruments
from src.cma_ui import cma
from src.indicators_ui import indicators_page


def render(page):
    require_login(show_logout=False)
    apply_theme();header();sidebar_notice()
    if page=='instruments':instruments()
    elif page=='home':home(None,None)
    else:
        p,q=real_data()
        if page=='indicators':indicators_page(p,q)
        elif page=='cma':cma(p,q)
    footer()
