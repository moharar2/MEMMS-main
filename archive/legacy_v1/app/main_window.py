"""
main_window.py
--------------
The MEMMS main window: dark navy sidebar, light content area, and a
QStackedWidget that swaps between pages.

This file wires up:
- The Translator (Arabic <-> English + RTL <-> LTR).
- Sidebar navigation buttons (one per section).
- The top bar (title, language switch, refresh).
- Page lifecycle (Dashboard is real, others are placeholders).
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .translations import LANG_AR, LANG_EN, TranslatableWidget, Translator

from .dashboard import DashboardPage
from .pages import PlaceholderPage
from .equipment_page import EquipmentPage
from .staff_page import StaffPage


class NavButton(QPushButton, TranslatableWidget):
    """
    A sidebar navigation button. It is also TranslatableWidget so we can
    refresh its label whenever the language changes.
    """

    def __init__(
        self,
        title_key: str,
        translator: Translator,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("NavButton")
        self.setProperty("class", "NavButton")
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self._title_key = title_key
        self._translator = translator
        self.retranslate_ui(self._translator.lang)

    def retranslate_ui(self, lang: str) -> None:
        self.setText(self._translator.t(self._title_key))


class MainWindow(QMainWindow, TranslatableWidget):
    """The top-level MEMMS window."""

    def __init__(self, translator: Translator) -> None:
        super().__init__()
        self._translator = translator

        self.setWindowTitle(self._translator.t("app.title"))
        self.resize(1100, 700)

        # Central widget: horizontal layout = [sidebar] + [content].
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self._build_sidebar())
        root_layout.addWidget(self._build_content(), 1)

        # Subscribe to language changes so every translatable widget refreshes.
        self._translator.language_changed.connect(self._on_language_changed)

        # Show the Dashboard by default.
        self._nav_buttons[0].setChecked(True)
        self._stack.setCurrentIndex(0)

    # ------------------------------------------------------------------
    # Sidebar
    # ------------------------------------------------------------------
    def _build_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(240)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        title = QLabel("MEMMS")
        title.setObjectName("sidebarTitle")
        subtitle = QLabel("Medical Equipment\nMaintenance System")
        subtitle.setObjectName("sidebarSubtitle")

        layout.addWidget(title)
        layout.addWidget(subtitle)

        # Use a QButtonGroup so only one nav button can be checked at a time.
        self._nav_group = QButtonGroup(self)
        self._nav_group.setExclusive(True)

        nav_specs = [
            ("nav.dashboard",       "dashboard"),
            ("nav.equipment",       "equipment"),
            ("nav.work_orders",     "work_orders"),
            ("nav.preventive",      "preventive"),
            ("nav.spare_parts",     "spare_parts"),
            ("nav.staff",           "staff"),
            ("nav.reports",         "reports"),
            ("nav.settings",        "settings"),
        ]

        self._nav_buttons: list[NavButton] = []
        self._nav_page_ids: list[str] = []
        for index, (title_key, page_id) in enumerate(nav_specs):
            btn = NavButton(title_key, self._translator, sidebar)
            # Give each button an explicit, predictable id so we can look
            # it up later if we need to.
            self._nav_group.addButton(btn, id=index)
            btn.clicked.connect(lambda _checked=False, pid=page_id: self._show_page(pid))
            layout.addWidget(btn)
            self._nav_buttons.append(btn)
            self._nav_page_ids.append(page_id)

        layout.addStretch(1)
        return sidebar

    # ------------------------------------------------------------------
    # Content area
    # ------------------------------------------------------------------
    def _build_content(self) -> QWidget:
        container = QWidget()
        container.setObjectName("contentArea")

        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._build_top_bar())
        self._stack = QStackedWidget()
        self._build_pages()
        layout.addWidget(self._stack, 1)
        return container

    def _build_top_bar(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("topBar")
        bar.setFixedHeight(64)

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(12)

        self._top_title = QLabel()
        self._top_title.setObjectName("pageTitle")

        layout.addWidget(self._top_title)
        layout.addStretch(1)

        self._refresh_button = QPushButton()
        self._refresh_button.setObjectName("refreshButton")
        self._refresh_button.setCursor(Qt.PointingHandCursor)
        self._refresh_button.clicked.connect(self._on_refresh_clicked)

        self._lang_button = QPushButton()
        self._lang_button.setObjectName("langButton")
        self._lang_button.setCursor(Qt.PointingHandCursor)
        self._lang_button.clicked.connect(self._on_language_button_clicked)

        layout.addWidget(self._refresh_button)
        layout.addWidget(self._lang_button)

        return bar

    def _build_pages(self) -> None:
        # Page 0: Dashboard — real implementation.
        self._dashboard = DashboardPage(self._translator)
        self._stack.addWidget(self._dashboard)

        # Page 1: Equipment registry — real implementation.
        self._equipment_page = EquipmentPage(self._translator)
        self._stack.addWidget(self._equipment_page)

        # Pages 2..4: Work orders, Preventive, Spare parts (Placeholders)
        self._page_work_orders = PlaceholderPage("placeholder.title.work_orders", self._translator)
        self._stack.addWidget(self._page_work_orders)

        self._page_preventive = PlaceholderPage("placeholder.title.preventive", self._translator)
        self._stack.addWidget(self._page_preventive)

        self._page_spare_parts = PlaceholderPage("placeholder.title.spare_parts", self._translator)
        self._stack.addWidget(self._page_spare_parts)

        # Page 5: Staff management — real implementation (Phase 3).
        self._staff_page = StaffPage(self._translator)
        self._stack.addWidget(self._staff_page)

        # Pages 6..7: Reports, Settings (Placeholders)
        self._page_reports = PlaceholderPage("placeholder.title.reports", self._translator)
        self._stack.addWidget(self._page_reports)

        self._page_settings = PlaceholderPage("placeholder.title.settings", self._translator)
        self._stack.addWidget(self._page_settings)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------
    def _show_page(self, page_id: str) -> None:
        page_order = [
            "dashboard", "equipment", "work_orders", "preventive",
            "spare_parts", "staff", "reports", "settings",
        ]
        if page_id in page_order:
            idx = page_order.index(page_id)
            self._stack.setCurrentIndex(idx)
            title_key = "dashboard.title" if page_id == "dashboard" else f"placeholder.title.{page_id}"
            self._top_title.setText(self._translator.t(title_key))

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------
    def _on_refresh_clicked(self) -> None:
        """Re-run queries and update view states."""
        self._dashboard.refresh_stats()
        self._equipment_page.refresh()
        self._staff_page.refresh()

    def _on_language_button_clicked(self) -> None:
        """Toggle between Arabic and English."""
        new_lang = LANG_EN if self._translator.lang == LANG_AR else LANG_AR
        self._translator.set_language(new_lang)

    def _on_language_changed(self, lang: str) -> None:
        """Refresh every translatable widget when the language flips."""
        self.setWindowTitle(self._translator.t("app.title"))
        self._top_title.setText(self._translator.t(self._current_page_title_key()))
        self._refresh_button.setText(self._translator.t("app.refresh"))
        self._lang_button.setText(
            self._translator.t("app.switch_to_english")
            if lang == LANG_AR
            else self._translator.t("app.switch_to_arabic")
        )

        # Re-translate every nav button + page in one sweep.
        for widget in TranslatableWidget.collect_translatable(self):
            widget.retranslate_ui(lang)

        # Refresh queries to keep texts and labels in sync.
        self._dashboard.refresh_stats()
        self._equipment_page.refresh()
        self._staff_page.refresh()

    def _current_page_title_key(self) -> str:
        """Return the translation key for the title of the visible page."""
        idx = self._stack.currentIndex()
        if idx == 0:
            return "dashboard.title"
        keys = [
            "placeholder.title.equipment",
            "placeholder.title.work_orders",
            "placeholder.title.preventive",
            "placeholder.title.spare_parts",
            "placeholder.title.staff",
            "placeholder.title.reports",
            "placeholder.title.settings",
        ]
        if 1 <= idx <= len(keys):
            return keys[idx - 1]
        return "dashboard.title"

    # ------------------------------------------------------------------
    # TranslatableWidget
    # ------------------------------------------------------------------
    def retranslate_ui(self, lang: str) -> None:
        # Called by collect_translatable. Keeps the top bar and title fresh.
        self._top_title.setText(self._translator.t(self._current_page_title_key()))
        self._refresh_button.setText(self._translator.t("app.refresh"))
        self._lang_button.setText(
            self._translator.t("app.switch_to_english")
            if lang == LANG_AR
            else self._translator.t("app.switch_to_arabic")
        )
