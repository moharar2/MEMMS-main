"""
Enterprise MainWindow integrating Sidebar, TopNavbar, Views stack, and Status Bar.
Zero emojis, clean architecture, and real dynamic bilingual switching.
Phases 3-7: All operational views registered and wired.
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QStatusBar, QLabel
)
from PySide6.QtCore import Qt, Signal
from src.core.i18n import tr, i18n
from src.services.auth_service import auth_service
from src.core.database import get_db
from src.ui.components.sidebar import Sidebar
from src.ui.components.top_navbar import TopNavbar
from src.ui.components.confirm_dialog import confirm_action
from src.ui.views import (
    # Phase 3 — Core
    DashboardView, EquipmentView, DepartmentsView,
    VendorsView, WorkOrdersView,
    # Phase 4 — Technicians
    TechniciansView,
    # Phase 5 — Preventive Maintenance
    PreventiveView,
    # Phase 6 — Inventory & Contracts
    InventoryView, ContractsView,
    # Phase 7 — System & Audit & User Management
    AuditLogsView, SettingsView, UsersView,
    # Phase 8 — Reports & Analytics
    ReportsView,
)


class MainWindow(QMainWindow):
    logout_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("MEMMS — " + tr("app.title"))
        self.resize(1180, 720)
        self.setMinimumSize(920, 560)
        self._is_navigating = False

        # Central Container
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        root_layout = QHBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. Sidebar Navigation
        self.sidebar = Sidebar()
        self.sidebar.navigation_changed.connect(self._on_nav_changed)
        root_layout.addWidget(self.sidebar)

        # 2. Main Content Area (Navbar + Stacked Views)
        content_area = QWidget()
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self.navbar = TopNavbar()
        self.navbar.logout_requested.connect(self._confirm_logout)
        content_layout.addWidget(self.navbar)

        self.stack = QStackedWidget()
        # View factories for lazy loading: (ViewClass, title_key)
        self.view_factories = {
            "dashboard": (DashboardView, "nav.dashboard"),
            "equipment": (EquipmentView, "nav.equipment"),
            "departments": (DepartmentsView, "nav.departments"),
            "work_orders": (WorkOrdersView, "nav.work_orders"),
            "vendors": (VendorsView, "nav.vendors"),
            "technicians": (TechniciansView, "nav.technicians"),
            "preventive": (PreventiveView, "nav.preventive"),
            "inventory": (InventoryView, "nav.inventory"),
            "contracts": (ContractsView, "nav.contracts"),
            "audit_logs": (AuditLogsView, "nav.audit_logs"),
            "users": (UsersView, "users.title"),
            "settings": (SettingsView, "nav.settings"),
            "reports": (ReportsView, "nav.reports"),
        }
        self.views = {}  # key -> (widget_instance, title_key)

        content_layout.addWidget(self.stack, stretch=1)
        root_layout.addWidget(content_area, stretch=1)

        # 4. Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.status_ready_lbl = QLabel(tr("common.system_ready"))
        self.status_ready_lbl.setStyleSheet(
            "color: #059669; font-weight: 600; padding-left: 10px; padding-right: 10px;"
        )
        self.status_bar.addWidget(self.status_ready_lbl)

        self.status_hosp_lbl = QLabel(tr("app.hospital_name"))
        self.status_hosp_lbl.setStyleSheet("color: #475569; padding-left: 10px; padding-right: 10px; font-weight: 600;")
        try:
            from src.models.hospital import Hospital
            with get_db() as db:
                hosp = db.query(Hospital).first()
                if hosp and hosp.name_ar:
                    self.status_hosp_lbl.setText(hosp.name_ar)
        except Exception:
            pass
        self.status_bar.addPermanentWidget(self.status_hosp_lbl)

        self.status_ver_lbl = QLabel(tr("app.version"))
        self.status_ver_lbl.setStyleSheet("color: #94A3B8; padding-left: 10px; padding-right: 10px;")
        self.status_bar.addPermanentWidget(self.status_ver_lbl)

        # Show Dashboard only initially on login
        self.navigate_to("dashboard")

    def __getattr__(self, name):
        """Allows direct attribute access to views (e.g. self.equipment_view) on-demand."""
        if name.endswith("_view"):
            key = name[:-5]
            if key in self.views:
                return self.views[key][0]
            elif key in self.view_factories:
                view_cls, title_key = self.view_factories[key]
                widget = view_cls()
                if key == "dashboard":
                    widget.navigate_requested.connect(self.navigate_to)
                self.stack.addWidget(widget)
                self.views[key] = (widget, title_key)
                return widget
        raise AttributeError(f"'MainWindow' object has no attribute '{name}'")

    def navigate_to(self, key: str):
        if self._is_navigating:
            return
        if key not in self.view_factories:
            return

        self._is_navigating = True
        try:
            # Lazy creation: create view only when navigated to for the first time
            if key not in self.views:
                view_cls, title_key = self.view_factories[key]
                widget = view_cls()
                if key == "dashboard":
                    widget.navigate_requested.connect(self.navigate_to)
                self.stack.addWidget(widget)
                self.views[key] = (widget, title_key)
            else:
                widget, title_key = self.views[key]
                # Refresh view data on navigation
                if hasattr(widget, "load_data"):
                    widget.load_data()
                elif hasattr(widget, "refresh"):
                    widget.refresh()
                elif hasattr(widget, "refresh_data"):
                    widget.refresh_data()

            self.stack.setCurrentWidget(widget)
            self.navbar.set_title(tr(title_key))
            self.sidebar.set_active(key)
        finally:
            self._is_navigating = False

    def _on_nav_changed(self, key: str):
        self.navigate_to(key)

    def _confirm_logout(self):
        if confirm_action(self, tr("app.logout"), tr("auth.logout_confirm"), is_danger=False):
            with get_db() as db:
                auth_service.logout(db)
            self.close()
            self.logout_requested.emit()

    def _on_locale_changed(self, new_locale: str):
        self.setWindowTitle("MEMMS — " + tr("app.title"))
        self.sidebar.retranslate_ui()
        self.status_ready_lbl.setText(tr("common.system_ready"))
        self.status_hosp_lbl.setText(tr("app.hospital_name"))
        self.status_ver_lbl.setText(tr("app.version"))

        # Re-translate all registered views
        for key, (widget, title_key) in self.views.items():
            if hasattr(widget, "retranslate_ui"):
                widget.retranslate_ui()

        # Update current view title in navbar
        current_widget = self.stack.currentWidget()
        for key, (widget, title_key) in self.views.items():
            if widget == current_widget:
                self.navbar.set_title(tr(title_key))
                break
