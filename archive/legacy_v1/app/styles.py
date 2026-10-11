"""
styles.py
---------
Qt Style Sheet (QSS) for MEMMS.

We keep all colors and spacing here so the rest of the code never talks
about hex codes. This is also the only file you need to edit to retheme
the app later.
"""

# A small palette of named colors so the QSS below stays readable.
COLOR_SIDEBAR_BG = "#1e293b"        # sleek slate-900 navy
COLOR_SIDEBAR_BG_ALT = "#334155"    # hover / pressed
COLOR_SIDEBAR_TEXT = "#f1f5f9"
COLOR_SIDEBAR_TEXT_MUTED = "#94a3b8"
COLOR_SIDEBAR_ACTIVE = "#2563eb"    # vivid blue accent

COLOR_CONTENT_BG = "#f8fafc"        # modern clean background
COLOR_CARD_BG = "#ffffff"
COLOR_CARD_BORDER = "#e2e8f0"
COLOR_TEXT_PRIMARY = "#0f172a"
COLOR_TEXT_SECONDARY = "#64748b"
COLOR_ACCENT = "#2563eb"
COLOR_ACCENT_HOVER = "#1d4ed8"
COLOR_ACCENT_SOFT = "#eff6ff"
COLOR_DANGER = "#dc2626"
COLOR_DANGER_HOVER = "#b91c1c"
COLOR_SUCCESS = "#16a34a"
COLOR_WARNING = "#d97706"

STYLESHEET = f"""
QMainWindow {{
    background-color: {COLOR_CONTENT_BG};
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
}}

QWidget {{
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
}}

/* ----- Sidebar ----- */
#sidebar {{
    background-color: {COLOR_SIDEBAR_BG};
    border: none;
}}

#sidebarTitle {{
    color: #ffffff;
    font-size: 20px;
    font-weight: 700;
    padding: 24px 20px 6px 20px;
    letter-spacing: 0.5px;
}}

#sidebarSubtitle {{
    color: {COLOR_SIDEBAR_TEXT_MUTED};
    font-size: 12px;
    padding: 0px 20px 22px 20px;
}}

NavButton {{
    background-color: transparent;
    color: {COLOR_SIDEBAR_TEXT};
    border: none;
    text-align: left;
    padding: 12px 20px;
    font-size: 13.5px;
    font-weight: 500;
    border-left: 4px solid transparent;
    border-radius: 0px;
}}

NavButton:hover {{
    background-color: {COLOR_SIDEBAR_BG_ALT};
    color: #ffffff;
}}

NavButton:checked {{
    background-color: #0f172a;
    border-left: 4px solid {COLOR_SIDEBAR_ACTIVE};
    color: #ffffff;
    font-weight: 600;
}}

/* ----- Top bar ----- */
#topBar {{
    background-color: #ffffff;
    border-bottom: 1px solid {COLOR_CARD_BORDER};
}}

#pageTitle {{
    color: {COLOR_TEXT_PRIMARY};
    font-size: 20px;
    font-weight: 700;
}}

#pageSubtitle {{
    color: {COLOR_TEXT_SECONDARY};
    font-size: 13px;
}}

/* ----- Content area ----- */
#contentArea {{
    background-color: {COLOR_CONTENT_BG};
}}

/* ----- Modern Cards ----- */
StatCard, .modern-card {{
    background-color: {COLOR_CARD_BG};
    border: 1px solid {COLOR_CARD_BORDER};
    border-radius: 12px;
}}

StatCard QLabel#cardTitle {{
    color: {COLOR_TEXT_SECONDARY};
    font-size: 13px;
    font-weight: 600;
}}

StatCard QLabel#cardValue {{
    color: {COLOR_TEXT_PRIMARY};
    font-size: 30px;
    font-weight: 700;
}}

StatCard QLabel#cardHint {{
    color: {COLOR_TEXT_SECONDARY};
    font-size: 12px;
}}

/* ----- Tables ----- */
QTableWidget {{
    background-color: #ffffff;
    border: 1px solid {COLOR_CARD_BORDER};
    border-radius: 10px;
    gridline-color: #f1f5f9;
    font-size: 13px;
    color: {COLOR_TEXT_PRIMARY};
    selection-background-color: #e0e7ff;
    selection-color: {COLOR_TEXT_PRIMARY};
    outline: none;
}}

QTableWidget::item {{
    padding: 10px 12px;
    border-bottom: 1px solid #f1f5f9;
}}

QTableWidget::item:selected {{
    background-color: #e0f2fe;
    color: #0369a1;
    font-weight: 600;
}}

QHeaderView::section {{
    background-color: #f8fafc;
    color: #475569;
    font-size: 12.5px;
    font-weight: 700;
    padding: 10px 12px;
    border: none;
    border-bottom: 2px solid {COLOR_CARD_BORDER};
}}

/* ----- Input Controls & ComboBoxes ----- */
QLineEdit, QComboBox, QTextEdit, QDateEdit {{
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
    color: {COLOR_TEXT_PRIMARY};
}}

QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QDateEdit:focus {{
    border: 2px solid {COLOR_ACCENT};
    background-color: #ffffff;
}}

/* ----- Buttons ----- */
QPushButton {{
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 600;
}}

QPushButton#btnPrimary, .btn-primary {{
    background-color: {COLOR_ACCENT};
    color: #ffffff;
    border: none;
}}
QPushButton#btnPrimary:hover, .btn-primary:hover {{
    background-color: {COLOR_ACCENT_HOVER};
}}

QPushButton#btnSecondary, .btn-secondary {{
    background-color: #ffffff;
    color: {COLOR_TEXT_PRIMARY};
    border: 1px solid {COLOR_CARD_BORDER};
}}
QPushButton#btnSecondary:hover, .btn-secondary:hover {{
    background-color: #f1f5f9;
    border-color: #cbd5e1;
}}

QPushButton#btnDanger, .btn-danger {{
    background-color: #fee2e2;
    color: {COLOR_DANGER};
    border: 1px solid #fecaca;
}}
QPushButton#btnDanger:hover, .btn-danger:hover {{
    background-color: {COLOR_DANGER};
    color: #ffffff;
}}

/* Top bar buttons */
QPushButton#langButton {{
    background-color: {COLOR_ACCENT};
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 7px 16px;
    font-size: 13px;
    font-weight: 600;
}}
QPushButton#langButton:hover {{
    background-color: {COLOR_ACCENT_HOVER};
}}

QPushButton#refreshButton {{
    background-color: #ffffff;
    color: {COLOR_TEXT_PRIMARY};
    border: 1px solid {COLOR_CARD_BORDER};
    border-radius: 8px;
    padding: 7px 16px;
    font-size: 13px;
    font-weight: 600;
}}
QPushButton#refreshButton:hover {{
    background-color: {COLOR_ACCENT_SOFT};
}}

/* Dialog styling */
QDialog {{
    background-color: #ffffff;
}}

/* Placeholder pages */
PlaceholderPage {{
    background-color: {COLOR_CARD_BG};
    border: 1px dashed {COLOR_CARD_BORDER};
    border-radius: 12px;
}}

PlaceholderPage QLabel#placeholderTitle {{
    color: {COLOR_TEXT_PRIMARY};
    font-size: 20px;
    font-weight: 700;
}}

PlaceholderPage QLabel#placeholderBody {{
    color: {COLOR_TEXT_SECONDARY};
    font-size: 14px;
}}

PlaceholderPage QLabel#placeholderBadge {{
    color: {COLOR_ACCENT};
    background-color: {COLOR_ACCENT_SOFT};
    border-radius: 12px;
    padding: 4px 12px;
    font-size: 12px;
    font-weight: 600;
}}
"""
