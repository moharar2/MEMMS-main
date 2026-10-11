"""
Enterprise Medical Equipment View:
Asset registry, multi-criteria filtering, KPI cards, and asset lifecycle actions.
Zero emojis, fully localized.
"""
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox,
    QPushButton, QLabel, QTableWidgetItem, QMessageBox, QFrame, QHeaderView
)
from PySide6.QtCore import Qt
from src.core.i18n import tr, i18n
from src.core.database import get_db
from src.services.equipment_service import equipment_service
from src.services.hospital_service import hospital_service
from src.services.auth_service import auth_service
from src.ui.theme.icons import icon
from src.ui.components.stat_card import StatCard
from src.ui.components.status_badge import StatusBadge
from src.ui.components.confirm_dialog import confirm_action
from src.ui.components.data_table import DataTable
from src.ui.components.action_button import ActionButton, create_actions_cell
from src.ui.views.equipment_dialog import EquipmentDialog
from src.ui.views.equipment_details_dialog import EquipmentDetailsDialog
from src.ui.views.transfer_dialog import TransferDialog
from src.models.equipment import Equipment


class EquipmentView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 14, 18, 14)
        main_layout.setSpacing(10)

        # 1. Header Frame
        header_frame = QFrame()
        h_layout = QHBoxLayout(header_frame)
        h_layout.setContentsMargins(0, 0, 0, 0)

        titles_box = QVBoxLayout()
        titles_box.setSpacing(2)
        self.title_lbl = QLabel(tr("equipment.title"))
        self.title_lbl.setStyleSheet("font-size: 16px; font-weight: 800; color: #0F172A;")

        self.subtitle_lbl = QLabel(tr("equipment.subtitle"))
        self.subtitle_lbl.setStyleSheet("font-size: 11px; color: #64748B; font-weight: 500;")

        titles_box.addWidget(self.title_lbl)
        titles_box.addWidget(self.subtitle_lbl)
        h_layout.addLayout(titles_box)

        main_layout.addWidget(header_frame)

        # 2. KPI Stat Cards Row
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(10)

        self.stat_total = StatCard(tr("dashboard.total_equipment"), "0", "equipment", "#0F766E")
        self.stat_total.setFixedHeight(72)
        self.stat_operational = StatCard(tr("dashboard.operational"), "0", "check", "#059669")
        self.stat_operational.setFixedHeight(72)
        self.stat_maintenance = StatCard(tr("dashboard.under_maintenance"), "0", "work_orders", "#D97706")
        self.stat_maintenance.setFixedHeight(72)
        self.stat_out_of_service = StatCard(tr("dashboard.out_of_service"), "0", "warning", "#DC2626")
        self.stat_out_of_service.setFixedHeight(72)

        stats_layout.addWidget(self.stat_total)
        stats_layout.addWidget(self.stat_operational)
        stats_layout.addWidget(self.stat_maintenance)
        stats_layout.addWidget(self.stat_out_of_service)
        main_layout.addLayout(stats_layout)

        # 3. Filter Bar
        filter_card = QFrame()
        filter_card.setProperty("frameShape", "card")
        filter_layout = QHBoxLayout(filter_card)
        filter_layout.setContentsMargins(12, 6, 12, 6)
        filter_layout.setSpacing(10)

        self.filter_lbl = QLabel(tr("common.filter") + ":")
        self.filter_lbl.setStyleSheet("font-weight: 700; color: #475569; font-size: 11px;")
        filter_layout.addWidget(self.filter_lbl)

        self.dept_filter = QComboBox()
        self.dept_filter.currentIndexChanged.connect(self.load_data)
        filter_layout.addWidget(self.dept_filter)

        self.status_filter = QComboBox()
        self.status_filter.currentIndexChanged.connect(self.load_data)
        filter_layout.addWidget(self.status_filter)

        self.risk_filter = QComboBox()
        self.risk_filter.currentIndexChanged.connect(self.load_data)
        filter_layout.addWidget(self.risk_filter)

        filter_layout.addStretch()

        self.reset_filter_btn = QPushButton(tr("common.clear_filter"))
        self.reset_filter_btn.setProperty("variant", "secondary")
        self.reset_filter_btn.setIcon(icon("clear", color="#64748B", size=12))
        self.reset_filter_btn.clicked.connect(self._reset_filters)
        filter_layout.addWidget(self.reset_filter_btn)

        main_layout.addWidget(filter_card)

        # 4. Main Data Table
        self.header_keys = [
            "equipment.asset_id",
            "equipment.name_ar",
            "equipment.category",
            "equipment.department",
            "equipment.status",
            "equipment.risk_level",
            "equipment.serial_number",
            "common.actions"
        ]
        headers = [tr(k) for k in self.header_keys]

        self.table_widget = DataTable()
        self.table_widget.set_headers(headers, self.header_keys)
        # 0: Asset ID, 1: Name, 2: Category, 3: Dept, 4: Status, 5: Risk, 6: Serial, 7: Actions
        self.table_widget.set_column_widths([110, 190, 150, 155, 110, 115, 120, 130], stretch_cols=[1, 2, 3])
        self.table_widget.table.verticalHeader().setDefaultSectionSize(38)

        self.table_widget.set_add_button_text("+ " + tr("equipment.add_button"))
        self.table_widget.set_add_button_visible(True)
        self.table_widget.search_changed.connect(lambda txt: self.load_data())
        self.table_widget.refresh_requested.connect(self.load_data)
        self.table_widget.add_requested.connect(self._on_add)
        self.table_widget.table.cellDoubleClicked.connect(self._on_table_double_clicked)
        main_layout.addWidget(self.table_widget, stretch=1)

        self._populate_filter_dropdowns()
        self.load_data()

    def _populate_filter_dropdowns(self):
        # Departments filter
        with get_db() as db:
            depts = hospital_service.get_departments(db)
            self.dept_filter.clear()
            self.dept_filter.addItem(tr("equipment.filter_all_departments"), None)
            for d in depts:
                dept_name = d.name_en if not i18n.is_rtl() and d.name_en else d.name_ar
                self.dept_filter.addItem(dept_name, d.id)

        # Status filter
        self.status_filter.clear()
        self.status_filter.addItem(tr("equipment.filter_all_statuses"), None)
        for st in ["operational", "under_maintenance", "out_of_service", "standby", "scrapped"]:
            self.status_filter.addItem(tr(f"status.{st}"), st)

        # Risk filter
        self.risk_filter.clear()
        self.risk_filter.addItem(tr("equipment.filter_all_risks"), None)
        for rk in ["high", "medium", "low"]:
            self.risk_filter.addItem(tr(f"risk.{rk}"), rk)

    def _reset_filters(self):
        self.dept_filter.setCurrentIndex(0)
        self.status_filter.setCurrentIndex(0)
        self.risk_filter.setCurrentIndex(0)
        self.table_widget.search_input.clear()
        self.load_data()

    def load_data(self):
        search_txt = self.table_widget.search_input.text().strip()
        dept_id = self.dept_filter.currentData()
        status = self.status_filter.currentData()
        risk = self.risk_filter.currentData()

        with get_db() as db:
            # Update KPI Cards
            stats = equipment_service.get_equipment_stats(db)
            self.stat_total.set_value(stats["total"])
            self.stat_operational.set_value(stats["operational"])
            self.stat_maintenance.set_value(stats["under_maintenance"])
            self.stat_out_of_service.set_value(stats["out_of_service"])

            # Query Records
            records = equipment_service.get_equipment_list(
                db=db,
                search_query=search_txt or None,
                department_id=dept_id,
                status=status,
                risk_level=risk
            )

            tbl = self.table_widget.table
            tbl.setRowCount(len(records))

            for row_idx, eq in enumerate(records):
                # 0: Asset ID
                it_id = QTableWidgetItem(eq.asset_number)
                it_id.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                tbl.setItem(row_idx, 0, it_id)

                # 1: Name
                eq_name = eq.name_ar or eq.name_en or "-"
                it_name = QTableWidgetItem(eq_name)
                it_name.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                tbl.setItem(row_idx, 1, it_name)

                # 2: Category & Model
                cat_text = f"{eq.category} {f'({eq.model})' if eq.model else ''}"
                it_cat = QTableWidgetItem(cat_text)
                it_cat.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                tbl.setItem(row_idx, 2, it_cat)

                # 3: Dept & Room
                dept_name = eq.department.name_ar if eq.department else "—"
                room_name = eq.location.room_name if eq.location else ""
                loc_display = f"{dept_name} {f'• {room_name}' if room_name else ''}"
                it_loc = QTableWidgetItem(loc_display)
                it_loc.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                tbl.setItem(row_idx, 3, it_loc)

                # 4: Status Badge
                badge = StatusBadge(eq.status)
                tbl.setCellWidget(row_idx, 4, badge)

                # 5: Risk Badge
                risk_badge = StatusBadge(f"risk_{eq.risk_level}")
                tbl.setCellWidget(row_idx, 5, risk_badge)

                # 6: Serial No
                it_sn = QTableWidgetItem(eq.serial_number)
                it_sn.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                tbl.setItem(row_idx, 6, it_sn)

                # 7: Action Buttons (View, Edit, Transfer, Delete)
                view_btn = ActionButton(
                    action_type="view",
                    tooltip=tr("common.view"),
                    callback=lambda _, e=eq: self._on_view(e.id)
                )
                edit_btn = ActionButton(
                    action_type="edit",
                    tooltip=tr("common.edit"),
                    callback=lambda _, e=eq: self._on_edit(e.id)
                )
                transfer_btn = ActionButton(
                    action_type="transfer",
                    tooltip=tr("common.transfer"),
                    callback=lambda _, e=eq: self._on_transfer(e.id)
                )
                delete_btn = ActionButton(
                    action_type="delete",
                    tooltip=tr("common.delete"),
                    callback=lambda _, e=eq: self._on_delete(e.id)
                )

                actions_widget = create_actions_cell(view_btn, edit_btn, transfer_btn, delete_btn)
                tbl.setCellWidget(row_idx, 7, actions_widget)

            self.table_widget.update_info(len(records), stats["total"])

    def _on_table_double_clicked(self, row: int, col: int):
        asset_item = self.table_widget.table.item(row, 0)
        if asset_item:
            asset_no = asset_item.text()
            with get_db() as db:
                eq = db.query(Equipment).filter_by(asset_number=asset_no).first()
                if eq:
                    self._on_view(eq.id)

    def _on_view(self, eq_id: int):
        with get_db() as db:
            eq = equipment_service.get_equipment_by_id(db, eq_id)
            dlg = EquipmentDetailsDialog(equipment=eq, parent=self)
            dlg.edit_requested.connect(self._on_edit)
            dlg.transfer_requested.connect(self._on_transfer)
            dlg.exec()

    def _on_add(self):
        dlg = EquipmentDialog(parent=self)
        if dlg.exec() == EquipmentDialog.DialogCode.Accepted:
            self.load_data()

    def _on_edit(self, eq_id: int):
        with get_db() as db:
            eq = equipment_service.get_equipment_by_id(db, eq_id)
            dlg = EquipmentDialog(equipment=eq, parent=self)
            if dlg.exec() == EquipmentDialog.DialogCode.Accepted:
                self.load_data()

    def _on_transfer(self, eq_id: int):
        with get_db() as db:
            eq = equipment_service.get_equipment_by_id(db, eq_id)
            dlg = TransferDialog(equipment=eq, parent=self)
            if dlg.exec() == TransferDialog.DialogCode.Accepted:
                self.load_data()

    def _on_delete(self, eq_id: int):
        if confirm_action(self, tr("dialog.confirm_title"), tr("dialog.confirm_delete_equipment")):
            user = auth_service.current_user
            try:
                with get_db() as db:
                    equipment_service.delete_equipment(db, user, eq_id)
                self.load_data()
            except Exception as e:
                QMessageBox.critical(self, tr("common.error"), str(e))

    def retranslate_ui(self):
        self.title_lbl.setText(tr("equipment.title"))
        self.subtitle_lbl.setText(tr("equipment.subtitle"))

        self.stat_total.set_title(tr("dashboard.total_equipment"))
        self.stat_operational.set_title(tr("dashboard.operational"))
        self.stat_maintenance.set_title(tr("dashboard.under_maintenance"))
        self.stat_out_of_service.set_title(tr("dashboard.out_of_service"))

        self.filter_lbl.setText(tr("common.filter") + ":")
        self.reset_filter_btn.setText(tr("common.clear_filter"))

        self._populate_filter_dropdowns()
        self.table_widget.retranslate_ui()
        self.load_data()
