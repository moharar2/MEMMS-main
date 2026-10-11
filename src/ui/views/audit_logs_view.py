"""
Audit Logs Viewer.
Immutable read-only view of all system activity, user operations, and asset changes.
Zero emojis, vector icons, bilingual support.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt, QTimer
from src.core.i18n import tr
from src.core.database import get_db
from src.models.audit import AuditLog
from src.ui.theme.icons import icon
from src.ui.components.data_table import DataTable


class AuditLogsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.all_logs = []
        self._setup_ui()
        QTimer.singleShot(0, self.refresh_data)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 14, 18, 14)
        main_layout.setSpacing(10)

        # Header
        header_layout = QHBoxLayout()
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)

        self.title_lbl = QLabel(tr("audit_logs.title"))
        self.title_lbl.setStyleSheet("font-size: 18px; font-weight: 800; color: #0F172A;")
        self.sub_lbl = QLabel(tr("audit_logs.subtitle"))
        self.sub_lbl.setStyleSheet("font-size: 12px; color: #64748B;")
        title_layout.addWidget(self.title_lbl)
        title_layout.addWidget(self.sub_lbl)
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        # Filter by entity type
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel(tr("audit_logs.entity_type") + ":"))
        self.entity_filter = QComboBox()
        self.entity_filter.addItem(tr("common.all"), "all")
        for etype in ["Equipment", "WorkOrder", "PMPlan", "PMExecution", "SparePart",
                      "InventoryTransaction", "Contract", "Technician", "Department", "Vendor"]:
            self.entity_filter.addItem(etype, etype)
        self.entity_filter.currentIndexChanged.connect(self._load_logs)
        filter_layout.addWidget(self.entity_filter)
        filter_layout.addStretch()
        main_layout.addLayout(filter_layout)

        # Table
        self.table_widget = DataTable()
        self.table_widget.set_add_button_visible(False)
        self.table_widget.set_search_placeholder(tr("common.search"))
        self.table_widget.search_changed.connect(self._on_search)
        self.table_widget.refresh_requested.connect(self.refresh_data)

        headers = [
            "#",
            tr("audit_logs.timestamp"),
            tr("audit_logs.action"),
            tr("audit_logs.entity_type"),
            tr("audit_logs.entity_id"),
            tr("audit_logs.user"),
            tr("audit_logs.details")
        ]
        self.table_widget.set_headers(headers)
        # 0: ID, 1: Time, 2: Action, 3: EntityType, 4: EntityID, 5: User, 6: Details
        self.table_widget.set_column_widths([45, 120, 100, 120, 80, 110, 250], stretch_cols=[6])
        self.table_widget.table.verticalHeader().setDefaultSectionSize(38)
        main_layout.addWidget(self.table_widget, stretch=1)

    def refresh_data(self):
        self._load_logs()

    def _load_logs(self):
        entity = self.entity_filter.currentData()
        with get_db() as db:
            query = db.query(AuditLog).order_by(AuditLog.created_at.desc())
            if entity and entity != "all":
                query = query.filter(AuditLog.entity_name == entity)
            logs = query.limit(500).all()
            self.all_logs = logs
            self._render_table(logs)

    def _render_table(self, logs):
        table = self.table_widget.table
        table.setRowCount(len(logs))

        for row, log in enumerate(logs):
            ts = log.created_at.strftime("%Y-%m-%d %H:%M") if log.created_at else "-"
            user_name = log.user.username if log.user else "system"

            it_id = QTableWidgetItem(str(log.id))
            it_id.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            table.setItem(row, 0, it_id)

            it_ts = QTableWidgetItem(ts)
            it_ts.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            table.setItem(row, 1, it_ts)

            it_act = QTableWidgetItem(log.action or "-")
            it_act.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            table.setItem(row, 2, it_act)

            it_ent = QTableWidgetItem(log.entity_name or "-")
            it_ent.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            table.setItem(row, 3, it_ent)

            it_eid = QTableWidgetItem(str(log.entity_id) if log.entity_id else "-")
            it_eid.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            table.setItem(row, 4, it_eid)

            it_usr = QTableWidgetItem(user_name)
            it_usr.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            table.setItem(row, 5, it_usr)

            it_det = QTableWidgetItem(log.details or "-")
            it_det.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            table.setItem(row, 6, it_det)

        self.table_widget.set_record_count(len(logs), len(logs))

    def _on_search(self, query: str):
        query = query.lower().strip()
        if not query:
            self._render_table(self.all_logs)
            return
        filtered = [
            log for log in self.all_logs
            if query in (log.action or "").lower()
            or query in (log.entity_type or "").lower()
            or query in (log.details or "").lower()
        ]
        self._render_table(filtered)

    def retranslate_ui(self):
        self.title_lbl.setText(tr("audit_logs.title"))
        self.sub_lbl.setText(tr("audit_logs.subtitle"))
        headers = [
            "#",
            tr("audit_logs.timestamp"),
            tr("audit_logs.action"),
            tr("audit_logs.entity_type"),
            tr("audit_logs.entity_id"),
            tr("audit_logs.user"),
            tr("audit_logs.details")
        ]
        self.table_widget.set_headers(headers)
        self.refresh_data()
