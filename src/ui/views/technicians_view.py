"""
Biomedical Engineering Staff View (Technicians).
Manage clinical engineers and biomedical technicians with specialization and status tracking.
Pure Arabic, RTL, zero emojis.
"""
from typing import List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QMessageBox, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt, QTimer
from src.core.i18n import tr
from src.core.database import get_db
from src.models.technician import Technician
from src.services.technician_service import technician_service
from src.ui.theme.icons import icon
from src.ui.components.stat_card import StatCard
from src.ui.components.status_badge import StatusBadge
from src.ui.components.data_table import DataTable
from src.ui.components.confirm_dialog import confirm_action
from src.ui.components.action_button import ActionButton, create_actions_cell
from src.ui.views.technician_dialog import TechnicianDialog


class TechniciansView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.all_techs: List[Technician] = []
        self._setup_ui()
        self.refresh_data()

    def load_data(self):
        self.refresh_data()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 14, 18, 14)
        main_layout.setSpacing(10)

        # 1. Header
        header_layout = QHBoxLayout()
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)

        self.title_lbl = QLabel("الكادر الفني والمهندسون الطبيون")
        self.title_lbl.setStyleSheet("font-size: 18px; font-weight: 800; color: #0F172A;")
        self.sub_lbl = QLabel("إدارة فريق مهندسي وفنيي الأجهزة الطبية وتوزيع المهام والصيانة")
        self.sub_lbl.setStyleSheet("font-size: 12px; color: #64748B;")
        title_layout.addWidget(self.title_lbl)
        title_layout.addWidget(self.sub_lbl)
        header_layout.addLayout(title_layout)
        header_layout.addStretch()

        main_layout.addLayout(header_layout)

        # 2. KPI Cards
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(10)

        self.card_total = StatCard("إجمالي الكادر الفني", "0", icon_name="technicians", accent_color="#0F766E")
        self.card_active = StatCard("الفنيون على رأس العمل", "0", icon_name="check", accent_color="#10B981")
        self.card_leave = StatCard("في إجازة / غير متاح", "0", icon_name="calendar", accent_color="#F59E0B")
        for card in (self.card_total, self.card_active, self.card_leave):
            card.setFixedHeight(72)

        kpi_layout.addWidget(self.card_total)
        kpi_layout.addWidget(self.card_active)
        kpi_layout.addWidget(self.card_leave)
        main_layout.addLayout(kpi_layout)

        # 3. Filters
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)

        filter_layout.addWidget(QLabel("حالة العمل:"))
        self.status_filter = QComboBox()
        self.status_filter.addItem("جميع الحالات", "all")
        self.status_filter.addItem("على رأس العمل (نشط)", "active")
        self.status_filter.addItem("في إجازة", "on_leave")
        self.status_filter.addItem("غير نشط", "inactive")
        self.status_filter.currentIndexChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.status_filter)

        filter_layout.addStretch()
        main_layout.addLayout(filter_layout)

        # 4. Data Table
        self.table_widget = DataTable()
        self.table_widget.set_search_placeholder("بحث برقم الموظف، الاسم، أو التخصص...")
        self.table_widget.search_changed.connect(self._on_search)
        self.table_widget.refresh_requested.connect(self.refresh_data)
        self.table_widget.set_add_button_text("+ إضافة مهندس / فني")
        self.table_widget.add_clicked.connect(self._open_add_dialog)

        headers = [
            "#",
            "الرقم الوظيفي",
            "الاسم الكامل",
            "المسمى والتخصص",
            "رقم الهوية",
            "القسم",
            "رقم الهاتف",
            "الحالة",
            "الإجراءات"
        ]
        self.table_widget.set_headers(headers)
        # 0: ID, 1: EmpID, 2: Name, 3: Spec/Title, 4: ID Masked, 5: Dept, 6: Phone, 7: Status, 8: Actions
        self.table_widget.set_column_widths([45, 95, 150, 160, 110, 110, 110, 90, 80], stretch_cols=[2, 3])
        self.table_widget.table.verticalHeader().setDefaultSectionSize(38)

        main_layout.addWidget(self.table_widget, stretch=1)

    def refresh_data(self):
        self._load_kpis()
        self._load_technicians()

    def _load_kpis(self):
        with get_db() as db:
            stats = technician_service.get_technician_statistics(db)
            self.card_total.set_value(str(stats.get("total_technicians", stats.get("total", 0))))
            self.card_active.set_value(str(stats.get("active", 0)))
            self.card_leave.set_value(str(stats.get("on_leave", 0)))

    def _load_technicians(self):
        status = self.status_filter.currentData()
        with get_db() as db:
            techs = technician_service.list_technicians(db, status=status)
            self.all_techs = techs
            self._render_table(techs)

    def _apply_filters(self):
        self._load_technicians()

    def _render_table(self, techs: List[Technician]):
        table = self.table_widget.table
        table.setRowCount(len(techs))

        for row, t in enumerate(techs):
            it_id = QTableWidgetItem(str(t.id))
            it_id.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            table.setItem(row, 0, it_id)

            it_emp = QTableWidgetItem(t.employee_id)
            it_emp.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            table.setItem(row, 1, it_emp)

            it_name = QTableWidgetItem(t.full_name)
            it_name.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            table.setItem(row, 2, it_name)

            title_spec = f"{t.job_title} • {t.specialization}" if t.job_title else (t.specialization or "—")
            it_spec = QTableWidgetItem(title_spec)
            it_spec.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            table.setItem(row, 3, it_spec)

            masked_id = technician_service.mask_id_number(t.id_number)
            it_id_num = QTableWidgetItem(masked_id)
            it_id_num.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            table.setItem(row, 4, it_id_num)

            dept_name = t.department.name_ar if t.department else "—"
            it_dept = QTableWidgetItem(dept_name)
            it_dept.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            table.setItem(row, 5, it_dept)

            it_ph = QTableWidgetItem(t.phone or "—")
            it_ph.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            table.setItem(row, 6, it_ph)

            # Status Badge
            badge = StatusBadge(t.status)
            table.setCellWidget(row, 7, badge)

            # Actions: Edit, Delete
            edit_btn = ActionButton(
                action_type="edit",
                tooltip="تعديل ملف الموظف",
                callback=lambda _, tid=t.id: self._open_edit_dialog(tid)
            )
            del_btn = ActionButton(
                action_type="delete",
                tooltip="تعطيل الموظف",
                callback=lambda _, tid=t.id: self._delete_tech(tid)
            )

            actions_widget = create_actions_cell(edit_btn, del_btn)
            table.setCellWidget(row, 8, actions_widget)

        self.table_widget.set_record_count(len(techs), len(techs))

    def _open_add_dialog(self):
        dlg = TechnicianDialog(parent=self)
        if dlg.exec():
            self.refresh_data()

    def _open_edit_dialog(self, tech_id: int):
        dlg = TechnicianDialog(tech_id=tech_id, parent=self)
        if dlg.exec():
            self.refresh_data()

    def _delete_tech(self, tech_id: int):
        if not confirm_action(self, "تأكيد الحذف", "هل أنت متأكد من حذف بيانات هذا المهندس / الفني؟"):
            return
        try:
            with get_db() as db:
                technician_service.delete_technician(db, tech_id)
            self.refresh_data()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))

    def _on_search(self, query: str):
        query = query.lower().strip()
        if not query:
            self._render_table(self.all_techs)
            return

        filtered = [
            t for t in self.all_techs
            if query in t.employee_id.lower()
            or query in t.full_name.lower()
            or query in (t.specialization or '').lower()
            or query in (t.phone or '').lower()
        ]
        self._render_table(filtered)

    def retranslate_ui(self):
        self.refresh_data()
