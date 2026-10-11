"""
Contracts & Warranty Management View.
Monitors service level agreements, manufacturer warranties, and vendor commitments.
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
from src.models.contract import Contract
from src.services.contract_service import contract_service
from src.ui.theme.icons import icon
from src.ui.components.stat_card import StatCard
from src.ui.components.status_badge import StatusBadge
from src.ui.components.data_table import DataTable
from src.ui.components.confirm_dialog import confirm_action
from src.ui.components.action_button import ActionButton, create_actions_cell
from src.ui.views.contract_dialog import ContractDialog


CONTRACT_TYPE_LABELS = {
    "comprehensive": "عقد صيانة شامل",
    "preventive_parts": "صيانة وقائية وقطع غيار",
    "preventive_only": "صيانة وقائية فقط",
    "parts_only": "توريد قطع غيار فقط",
    "warranty": "ضمان الشركة المصنعة",
    "supply_service": "توريد وخدمة",
    "maintenance": "صيانة وقائية وعلاجية",
    "supply": "توريد قطع غيار ومستهلكات",
    "turnkey": "عقد شامل ومباشر",
}


class ContractsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.all_contracts: List[Contract] = []
        self._setup_ui()
        QTimer.singleShot(0, self.refresh_data)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 14, 18, 14)
        main_layout.setSpacing(10)

        # 1. Header
        header_layout = QHBoxLayout()
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)

        self.title_lbl = QLabel("إدارة عقود الصيانة والضمان")
        self.title_lbl.setStyleSheet("font-size: 18px; font-weight: 800; color: #0F172A;")
        self.sub_lbl = QLabel("متابعة اتفاقيات مستوى الخدمة (SLA)، عقود الصيانة السنوية، وضمان الأجهزة الطبية")
        self.sub_lbl.setStyleSheet("font-size: 12px; color: #64748B;")
        title_layout.addWidget(self.title_lbl)
        title_layout.addWidget(self.sub_lbl)
        header_layout.addLayout(title_layout)
        header_layout.addStretch()

        main_layout.addLayout(header_layout)

        # 2. KPI Cards
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(10)

        self.card_active = StatCard("العقود السارية", "0", icon_name="contracts", accent_color="#0F766E")
        self.card_expiring = StatCard("عقود توشك على الانتهاء", "0", icon_name="warning", accent_color="#F59E0B")
        self.card_val = StatCard("إجمالي القيمة التعاقدية", "0 ر.س", icon_name="dollar", accent_color="#2563EB")
        for card in (self.card_active, self.card_expiring, self.card_val):
            card.setFixedHeight(72)

        kpi_layout.addWidget(self.card_active)
        kpi_layout.addWidget(self.card_expiring)
        kpi_layout.addWidget(self.card_val)
        main_layout.addLayout(kpi_layout)

        # 3. Filters
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)

        filter_layout.addWidget(QLabel("نوع العقد:"))
        self.type_filter = QComboBox()
        self.type_filter.addItem("جميع أنواع العقود", "all")
        self.type_filter.addItem("عقد صيانة شامل", "comprehensive")
        self.type_filter.addItem("عقد صيانة وقائية وقطع غيار", "preventive_parts")
        self.type_filter.addItem("عقد صيانة وقائية فقط", "preventive_only")
        self.type_filter.addItem("عقد توريد قطع غيار فقط", "parts_only")
        self.type_filter.addItem("عقد ضمان الشركة المصنعة", "warranty")
        self.type_filter.addItem("عقد توريد وخدمة", "supply_service")
        self.type_filter.currentIndexChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.type_filter)

        self.active_only_btn = QPushButton("العقود السارية فقط")
        self.active_only_btn.setCheckable(True)
        self.active_only_btn.clicked.connect(self._apply_filters)
        filter_layout.addWidget(self.active_only_btn)

        filter_layout.addStretch()
        main_layout.addLayout(filter_layout)

        # 4. Data Table
        self.table_widget = DataTable()
        self.table_widget.set_search_placeholder("بحث برقم العقد، العنوان، أو اسم الشركة الموردة...")
        self.table_widget.search_changed.connect(self._on_search)
        self.table_widget.refresh_requested.connect(self.refresh_data)
        self.table_widget.set_add_button_text("+ إضافة عقد")
        self.table_widget.add_clicked.connect(self._open_add_dialog)

        headers = [
            "#",
            "رقم العقد",
            "عنوان / موضوع العقد",
            "الشركة / المورد",
            "نوع العقد",
            "تاريخ البداية",
            "تاريخ الانتهاء",
            "قيمة العقد",
            "الحالة",
            "الإجراءات"
        ]
        self.table_widget.set_headers(headers)
        # 0: ID, 1: Contract#, 2: Title, 3: Vendor, 4: Type, 5: Start, 6: End, 7: Value, 8: Status, 9: Actions
        self.table_widget.set_column_widths([45, 95, 170, 140, 120, 90, 90, 100, 85, 80], stretch_cols=[2, 3])
        self.table_widget.table.verticalHeader().setDefaultSectionSize(38)

        main_layout.addWidget(self.table_widget, stretch=1)

    def refresh_data(self):
        self._load_kpis()
        self._load_contracts()

    def _load_kpis(self):
        with get_db() as db:
            stats = contract_service.get_contract_statistics(db)
            self.card_active.set_value(str(stats["active"]))
            self.card_expiring.set_value(str(stats["expiring_soon"]))
            self.card_val.set_value(f"{stats['total_value']:,.2f} ر.س")

    def _load_contracts(self):
        c_type = self.type_filter.currentData()
        active_only = self.active_only_btn.isChecked()

        with get_db() as db:
            contracts = contract_service.list_contracts(db, contract_type=c_type, active_only=active_only)
            self.all_contracts = contracts
            self._render_table(contracts)

    def _apply_filters(self):
        self._load_contracts()

    def _render_table(self, contracts: List[Contract]):
        table = self.table_widget.table
        table.setRowCount(len(contracts))

        for row, c in enumerate(contracts):
            it_id = QTableWidgetItem(str(c.id))
            it_id.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            table.setItem(row, 0, it_id)

            it_num = QTableWidgetItem(c.contract_number)
            it_num.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            table.setItem(row, 1, it_num)

            it_title = QTableWidgetItem(c.title)
            it_title.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            table.setItem(row, 2, it_title)

            v_name = c.vendor.name if c.vendor else "—"
            it_vend = QTableWidgetItem(v_name)
            it_vend.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            table.setItem(row, 3, it_vend)

            type_text = CONTRACT_TYPE_LABELS.get(c.contract_type, c.contract_type or "—")
            it_type = QTableWidgetItem(type_text)
            it_type.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            table.setItem(row, 4, it_type)

            it_st = QTableWidgetItem(str(c.start_date))
            it_st.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            table.setItem(row, 5, it_st)

            it_end = QTableWidgetItem(str(c.end_date))
            it_end.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            table.setItem(row, 6, it_end)

            cost_val = f"{c.cost:,.2f} ر.س" if c.cost else "—"
            it_cost = QTableWidgetItem(cost_val)
            it_cost.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            table.setItem(row, 7, it_cost)

            # Status Badge
            st = "active" if c.is_active else "inactive"
            badge = StatusBadge(st)
            table.setCellWidget(row, 8, badge)

            # Actions: Edit, Delete
            edit_btn = ActionButton(
                action_type="edit",
                tooltip="تعديل بيانات العقد",
                callback=lambda _, cid=c.id: self._open_edit_dialog(cid)
            )
            del_btn = ActionButton(
                action_type="delete",
                tooltip="حذف العقد",
                callback=lambda _, cid=c.id: self._delete_contract(cid)
            )

            actions_widget = create_actions_cell(edit_btn, del_btn)
            table.setCellWidget(row, 9, actions_widget)

        self.table_widget.set_record_count(len(contracts), len(contracts))

    def _open_add_dialog(self):
        dlg = ContractDialog(parent=self)
        if dlg.exec():
            self.refresh_data()

    def _open_edit_dialog(self, contract_id: int):
        dlg = ContractDialog(contract_id=contract_id, parent=self)
        if dlg.exec():
            self.refresh_data()

    def _delete_contract(self, contract_id: int):
        if not confirm_action(self, "تأكيد الحذف", "هل أنت متأكد من حذف هذا العقد؟"):
            return
        try:
            with get_db() as db:
                contract_service.delete_contract(db, contract_id)
            self.refresh_data()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))

    def _on_search(self, query: str):
        query = query.lower().strip()
        if not query:
            self._render_table(self.all_contracts)
            return

        filtered = [
            c for c in self.all_contracts
            if query in c.contract_number.lower()
            or query in c.title.lower()
            or (c.vendor and query in c.vendor.name.lower())
            or query in CONTRACT_TYPE_LABELS.get(c.contract_type, "").lower()
        ]
        self._render_table(filtered)

    def retranslate_ui(self):
        self.refresh_data()
