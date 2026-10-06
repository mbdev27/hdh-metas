from src.auth import require_login
from src.theme import apply_theme,header,footer
from src.sih_ui import render_sih
require_login(show_logout=False)
apply_theme()
header()
render_sih()
footer()
