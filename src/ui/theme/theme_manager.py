import os
from src.ui.theme.tokens import LIGHT_PALETTE, FONT_FAMILY, ColorPalette

try:
    from PySide6.QtWidgets import QApplication
    HAS_PYSIDE = True
except ImportError:
    HAS_PYSIDE = False
    QApplication = None

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets").replace("\\", "/")


def ensure_theme_assets():
    os.makedirs(ASSETS_DIR, exist_ok=True)
    cal_png = os.path.join(ASSETS_DIR, "calendar.png")
    prev_png = os.path.join(ASSETS_DIR, "chevron_right.png")
    next_png = os.path.join(ASSETS_DIR, "chevron_left.png")
    
    if not (os.path.exists(cal_png) and os.path.exists(prev_png) and os.path.exists(next_png)):
        try:
            import qtawesome as qta
            qta.icon("fa5s.calendar-alt", color="#0F766E").pixmap(16, 16).save(cal_png, "PNG")
            qta.icon("fa5s.chevron-right", color="#FFFFFF").pixmap(14, 14).save(prev_png, "PNG")
            qta.icon("fa5s.chevron-left", color="#FFFFFF").pixmap(14, 14).save(next_png, "PNG")
        except Exception:
            pass


class ThemeManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ThemeManager, cls).__new__(cls)
            cls._instance.current_theme = "light"
            ensure_theme_assets()
        return cls._instance

    def get_palette(self) -> ColorPalette:
        return LIGHT_PALETTE

    def set_theme(self, theme_name: str = "light"):
        self.current_theme = "light"
        self.apply_theme()

    def generate_qss(self) -> str:
        c = self.get_palette()
        ensure_theme_assets()
        cal_path = os.path.join(ASSETS_DIR, "calendar.png").replace("\\", "/")
        prev_path = os.path.join(ASSETS_DIR, "chevron_right.png").replace("\\", "/")
        next_path = os.path.join(ASSETS_DIR, "chevron_left.png").replace("\\", "/")

        return f"""
        /* ==========================================================================
           1. Global Window & Core Typography
           ========================================================================== */
        QWidget {{
            font-family: {FONT_FAMILY};
            font-size: 13px;
            color: {c.TEXT_PRIMARY};
            background-color: transparent;
        }}

        QMainWindow, QDialog {{
            background-color: {c.BG_MAIN};
        }}

        /* Sidebar Enterprise Dark Navy Surface */
        QWidget#SidebarRoot, 
        QWidget#SidebarScrollContent, 
        QScrollArea#SidebarScroll, 
        QScrollArea#SidebarScroll > QWidget, 
        QScrollArea#SidebarScroll > QWidget > QWidget {{
            background-color: #0F172A;
            border: none;
        }}

        /* ==========================================================================
           2. Form Controls & Inputs (High Contrast, Pure White, Sharp Legibility)
           ========================================================================== */
        QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QTimeEdit, QDateTimeEdit {{
            background-color: #FFFFFF;
            color: #0F172A;
            border: 1px solid #CBD5E1;
            border-radius: 6px;
            padding: 7px 12px;
            font-size: 13px;
            selection-background-color: #0F766E;
            selection-color: #FFFFFF;
        }}

        QLineEdit:hover, QTextEdit:hover, QPlainTextEdit:hover, QSpinBox:hover, QDoubleSpinBox:hover {{
            border-color: #94A3B8;
        }}

        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
            border: 1.5px solid #0F766E;
            background-color: #FFFFFF;
        }}

        QLineEdit:disabled, QTextEdit:disabled, QSpinBox:disabled, QDateEdit:disabled {{
            background-color: #F1F5F9;
            color: #94A3B8;
            border-color: #E2E8F0;
        }}

        /* ComboBox */
        QComboBox {{
            background-color: #FFFFFF;
            color: #0F172A;
            border: 1px solid #CBD5E1;
            border-radius: 6px;
            padding: 7px 12px;
            min-height: 20px;
            font-size: 13px;
        }}

        QComboBox:hover {{
            border-color: #94A3B8;
        }}

        QComboBox:focus {{
            border: 1.5px solid #0F766E;
        }}

        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top left;
            width: 24px;
            border-left-width: 0px;
            border-top-right-radius: 0px;
            border-bottom-right-radius: 0px;
        }}

        QComboBox QAbstractItemView {{
            background-color: #FFFFFF;
            color: #0F172A;
            border: 1px solid #CBD5E1;
            border-radius: 6px;
            selection-background-color: #CCFBF1;
            selection-color: #0F766E;
            padding: 4px;
            outline: none;
        }}

        /* ==========================================================================
           2.1 DateEdit & Modern Medical Calendar Widget
           ========================================================================== */
        QDateEdit {{
            background-color: #FFFFFF;
            color: #0F172A;
            border: 1px solid #CBD5E1;
            border-radius: 6px;
            padding: 6px 10px;
            padding-left: 32px;
            font-size: 13px;
            min-height: 22px;
        }}

        QDateEdit:hover {{
            border-color: #0F766E;
        }}

        QDateEdit:focus {{
            border: 1.5px solid #0F766E;
            background-color: #FFFFFF;
        }}

        QDateEdit::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top left;
            width: 28px;
            background-color: #F0FDFA;
            border-right: 1px solid #CBD5E1;
            border-top-left-radius: 5px;
            border-bottom-left-radius: 5px;
        }}

        QDateEdit::drop-down:hover {{
            background-color: #CCFBF1;
        }}

        QDateEdit::down-arrow {{
            image: url("{cal_path}");
            width: 15px;
            height: 15px;
        }}

        /* Calendar Widget Container */
        QCalendarWidget {{
            background-color: #FFFFFF;
            border: 1px solid #CBD5E1;
            border-radius: 10px;
        }}

        /* Calendar Top Navigation Bar */
        QCalendarWidget QWidget#qt_calendar_navigationbar {{
            background-color: #0F766E;
            border-top-left-radius: 9px;
            border-top-right-radius: 9px;
            min-height: 40px;
            max-height: 40px;
            padding: 2px 8px;
        }}

        /* Navigation Buttons (Prev/Next Month, Month/Year selectors) */
        QCalendarWidget QToolButton {{
            color: #FFFFFF;
            font-size: 13px;
            font-weight: 700;
            background-color: transparent;
            border: 1px solid transparent;
            border-radius: 6px;
            padding: 4px 10px;
            min-height: 26px;
        }}

        QCalendarWidget QToolButton:hover {{
            background-color: #115E59;
            border-color: #14B8A6;
        }}

        QCalendarWidget QToolButton:pressed {{
            background-color: #134E4A;
        }}

        QCalendarWidget QToolButton#qt_calendar_prevmonth {{
            qproperty-icon: none;
            image: url("{prev_path}");
            min-width: 28px;
            max-width: 28px;
        }}

        QCalendarWidget QToolButton#qt_calendar_nextmonth {{
            qproperty-icon: none;
            image: url("{next_path}");
            min-width: 28px;
            max-width: 28px;
        }}

        /* Year SpinBox inside Calendar */
        QCalendarWidget QSpinBox {{
            background-color: #FFFFFF;
            color: #0F172A;
            border: 1px solid #CBD5E1;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 700;
            padding: 2px 8px;
            selection-background-color: #0F766E;
            selection-color: #FFFFFF;
        }}

        /* Month Popup Menu inside Calendar */
        QCalendarWidget QMenu {{
            background-color: #FFFFFF;
            color: #0F172A;
            border: 1px solid #CBD5E1;
            border-radius: 8px;
            padding: 4px;
            font-size: 13px;
        }}

        QCalendarWidget QMenu::item {{
            padding: 6px 18px;
            border-radius: 4px;
        }}

        QCalendarWidget QMenu::item:selected {{
            background-color: #CCFBF1;
            color: #0F766E;
            font-weight: 700;
        }}

        /* Calendar Dates Table Grid */
        QCalendarWidget QTableView {{
            background-color: #FFFFFF;
            alternate-background-color: #FFFFFF;
            selection-background-color: #0F766E;
            selection-color: #FFFFFF;
            border: none;
            outline: none;
            font-size: 13px;
            font-weight: 600;
            color: #0F172A;
        }}

        /* Day of Week Headers (Sa, Su, Mo, Tu, We, Th, Fr) */
        QCalendarWidget QHeaderView::section {{
            background-color: #F8FAFC;
            color: #475569;
            font-size: 12px;
            font-weight: 800;
            border: none;
            border-bottom: 2px solid #E2E8F0;
            padding: 6px 0px;
            min-height: 28px;
            text-align: center;
        }}

        /* Calendar Day Cells */
        QCalendarWidget QAbstractItemView:enabled {{
            color: #0F172A;
            selection-background-color: #0F766E;
            selection-color: #FFFFFF;
        }}

        QCalendarWidget QAbstractItemView:disabled {{
            color: #CBD5E1;
        }}

        /* ==========================================================================
           3. Buttons (Primary, Secondary, Danger, Action Buttons)
           ========================================================================== */
        QPushButton {{
            background-color: {c.PRIMARY};
            color: #FFFFFF;
            border: 1px solid {c.PRIMARY};
            border-radius: 6px;
            padding: 7px 16px;
            font-weight: 700;
            font-size: 13px;
            outline: none;
            min-height: 20px;
        }}

        QPushButton:hover {{
            background-color: {c.PRIMARY_HOVER};
            border-color: {c.PRIMARY_HOVER};
        }}

        QPushButton:pressed {{
            background-color: {c.PRIMARY_ACTIVE};
            border-color: {c.PRIMARY_ACTIVE};
        }}

        QPushButton:disabled {{
            background-color: #E2E8F0;
            border-color: #E2E8F0;
            color: #94A3B8;
        }}

        QPushButton[variant="secondary"] {{
            background-color: #FFFFFF;
            color: #334155;
            border: 1px solid #CBD5E1;
            font-weight: 600;
        }}

        QPushButton[variant="secondary"]:hover {{
            background-color: #F8FAFC;
            border-color: #94A3B8;
            color: #0F172A;
        }}

        QPushButton[variant="danger"] {{
            background-color: #DC2626;
            color: #FFFFFF;
            border: 1px solid #DC2626;
        }}

        QPushButton[variant="danger"]:hover {{
            background-color: #B91C1C;
            border-color: #B91C1C;
        }}

        /* Action buttons inside tables - zero padding override to prevent clipping */
        QPushButton[actionButton="true"] {{
            min-height: 0px;
            min-width: 0px;
            font-size: 11px;
            font-weight: 600;
            outline: none;
        }}


        /* ==========================================================================
           4. Card Surfaces & GroupBoxes
           ========================================================================== */
        QFrame[frameShape="card"], QFrame[property_frameShape="card"] {{
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 10px;
        }}

        QGroupBox {{
            font-weight: 700;
            font-size: 13px;
            color: #0F172A;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            margin-top: 12px;
            padding-top: 18px;
            padding-left: 14px;
            padding-right: 14px;
            padding-bottom: 14px;
            background-color: #FFFFFF;
        }}

        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top right;
            padding: 0 8px;
            color: #0F766E;
        }}

        /* ==========================================================================
           5. Tables & Grids (Clear, Professional, High-contrast)
           ========================================================================== */
        QTableWidget, QTableView {{
            background-color: #FFFFFF;
            alternate-background-color: #F8FAFC;
            color: #0F172A;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            gridline-color: #F1F5F9;
            selection-background-color: #CCFBF1;
            selection-color: #0F766E;
            outline: none;
            font-size: 13px;
        }}

        QTableWidget::item, QTableView::item {{
            padding: 6px 10px;
            border-bottom: 1px solid #F1F5F9;
            text-align: right;
        }}

        QHeaderView::section {{
            background-color: #F8FAFC;
            color: #334155;
            font-size: 12px;
            font-weight: 700;
            padding: 8px 8px;
            border: none;
            border-bottom: 2px solid #CBD5E1;
            border-left: 1px solid #F1F5F9;
            text-align: center;
        }}

        /* ==========================================================================
           6. Scrollbars & Sliders
           ========================================================================== */
        QScrollBar:vertical {{
            background: #F1F5F9;
            width: 8px;
            border-radius: 4px;
            margin: 0;
        }}

        QScrollBar::handle:vertical {{
            background: #CBD5E1;
            border-radius: 4px;
            min-height: 24px;
        }}

        QScrollBar::handle:vertical:hover {{
            background: #94A3B8;
        }}

        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}

        QScrollBar:horizontal {{
            background: #F1F5F9;
            height: 8px;
            border-radius: 4px;
            margin: 0;
        }}

        QScrollBar::handle:horizontal {{
            background: #CBD5E1;
            border-radius: 4px;
            min-width: 24px;
        }}

        QScrollBar::handle:horizontal:hover {{
            background: #94A3B8;
        }}

        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}

        /* ==========================================================================
           7. Tab Widget
           ========================================================================== */
        QTabWidget::pane {{
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            background: #FFFFFF;
            top: -1px;
        }}

        QTabBar::tab {{
            background: #F8FAFC;
            color: #64748B;
            padding: 10px 22px;
            margin-left: 4px;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            font-weight: 600;
            font-size: 13px;
            border: 1px solid #E2E8F0;
            border-bottom: none;
        }}

        QTabBar::tab:selected {{
            background: #FFFFFF;
            color: #0F766E;
            font-weight: 700;
            border-top: 2px solid #0F766E;
        }}

        QTabBar::tab:hover:!selected {{
            color: #0F172A;
            background: #F1F5F9;
        }}

        /* ==========================================================================
           8. Status Bar & Tooltips
           ========================================================================== */
        QStatusBar {{
            background-color: #FFFFFF;
            color: #475569;
            border-top: 1px solid #E2E8F0;
            font-size: 12px;
            padding: 4px 10px;
        }}

        QToolTip {{
            background-color: #0F172A;
            color: #FFFFFF;
            border: 1px solid #1E293B;
            border-radius: 4px;
            padding: 6px 10px;
            font-size: 12px;
        }}
        """

    def apply_theme(self):
        if HAS_PYSIDE and QApplication.instance() is not None:
            qss = self.generate_qss()
            QApplication.instance().setStyleSheet(qss)


theme_manager = ThemeManager()
