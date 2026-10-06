from src.auth import require_login
from src.theme import apply_theme,header,footer
from src.sih_ui import render_sih
from src.safe_ui import run_safely
require_login(show_logout=False)
apply_theme()
header()
run_safely(render_sih)
footer()
