"""
Spare Parts & Biomedical Inventory View.
Real-time tracking of spare parts, low stock thresholds, and stock movements.
Pure Arabic, RTL, zero emojis.
"""
from typing import List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QMessageBox, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor
from src.core.i18n import tr
from src.core.database import get_db
from src.models.inventory import SparePart
from src.services.inventory_service import inventory_service
from src.ui.theme.icons import icon
from src.ui.components.stat_card import StatCard
from src.ui.components.data_table import DataTable
from src.ui.components.confirm_dialog import confirm_action
from src.ui.components.action_button import ActionButton, create_actions_cell
from src.ui.views.spare_part_dialog import SparePartDialog
from src.ui.views.stock_transaction_dialog import StockTransactionDialog


class InventoryView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.all_parts: List[SparePart] = []
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

        self.title_lbl = QLabel("إدارة المستودع وقطع الغيار")
        self.title_lbl.setStyleSheet("font-size: 18px; font-weight: 800; color: #0F172A;")
        self.sub_lbl = QLabel("متابعة مخزون قطع الغيار الطبية، أرصدة الأمان، وحركات الصرف والتوريد")
        self.sub_lbl.setStyleSheet("font-size: 12px; color: #64748B;")

        title_layout.addWidget(self.title_lbl)
        title_layout.addWidget(self.sub_lbl)
        header_layout.addLayout(title_layout)
        header_layout.addStretch()

        main_layout.addLayout(header_layout)

        # 2. KPI Cards
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(10)

        self.card_total = StatCard("إجمالي أصناف قطع الغيار", "0", icon_name="inventory", accent_color="#0F766E")
        self.card_low = StatCard("قطع أوشكت على النفاد", "0", icon_name="warning", accent_color="#EF4444")
        self.card_val = StatCard("إجمالي القيمة التقديرية للمخزون", "0 ر.س", icon_name="dollar", accent_color="#2563EB")
        for card in (self.card_total, self.card_low, self.card_val):
            card.setFixedHeight(72)

        kpi_layout.addWidget(self.card_total)
        kpi_layout.addWidget(self.card_low)
        kpi_layout.addWidget(self.card_val)
        main_layout.addLayout(kpi_layout)

        # 3. Filters
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)

        filter_layout.addWidget(QLabel("التصنيف:"))
        self.cat_filter = QComboBox()
        self.cat_filter.addItem("جميع التصنيفات", "all")
        self.cat_filter.currentIndexChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.cat_filter)

        self.low_stock_btn = QPushButton("عرض الأصناف منخفضة الرصيد فقط")
        self.low_stock_btn.setCheckable(True)
        self.low_stock_btn.setIcon(icon("warning", color="#EF4444", size=14))
        self.low_stock_btn.clicked.connect(self._apply_filters)
        filter_layout.addWidget(self.low_stock_btn)

        filter_layout.addStretch()
        main_layout.addLayout(filter_layout)

        # 4. Data Table
        self.table_widget = DataTable()
        self.table_widget.set_search_placeholder("بحث برقم القطعة، الاسم، أو موقع التخزين...")
        self.table_widget.search_changed.connect(self._on_search)
        self.table_widget.refresh_requested.connect(self.refresh_data)
        self.table_widget.set_add_button_text("+ إضافة قطعة غيار")
        self.table_widget.add_clicked.connect(self._open_add_dialog)

        headers = [
            "#",
            "رقم القطعة / الكود",
            "اسم قطعة الغيار",
            "التصنيف",
            "موقع التخزين (الرف)",
            "الكمية المتوفرة",
            "حد إعادة الطلب",
            "سعر الوحدة",
            "الإجراءات"
        ]
        self.table_widget.set_headers(headers)
        # 0: ID, 1: Part#, 2: Name, 3: Category, 4: Bin, 5: Qty, 6: Min, 7: Price, 8: Actions
        self.table_widget.set_column_widths([45, 115, 185, 130, 125, 115, 110, 125, 155], stretch_cols=[2])
        self.table_widget.table.verticalHeader().setDefaultSectionSize(38)

        main_layout.addWidget(self.table_widget, stretch=1)

    def refresh_data(self):
        self._load_kpis()
        self._load_categories()
        self._load_parts()

    def _load_kpis(self):
        with get_db() as db:
            stats = inventory_service.get_inventory_statistics(db)
            self.card_total.set_value(str(stats["total_parts"]))
            self.card_low.set_value(str(stats["low_stock_count"]))
            self.card_val.set_value(f"{stats['total_value']:,.2f} ر.س")

    def _load_categories(self):
        curr = self.cat_filter.currentData()
        self.cat_filter.blockSignals(True)
        self.cat_filter.clear()
        self.cat_filter.addItem("جميع التصنيفات", "all")

        with get_db() as db:
            cats = [c[0] for c in db.query(SparePart.category).distinct().filter(SparePart.is_active.is_(True)).all()]
            for cat in sorted(cats):
                if cat:
                    self.cat_filter.addItem(cat, cat)

        idx = self.cat_filter.findData(curr)
        if idx >= 0:
            self.cat_filter.setCurrentIndex(idx)
        self.cat_filter.blockSignals(False)

    def _load_parts(self):
        cat = self.cat_filter.currentData()
        low_only = self.low_stock_btn.isChecked()

        with get_db() as db:
            parts = inventory_service.list_spare_parts(db, low_stock_only=low_only, category=cat)
            self.all_parts = parts
            self._render_table(parts)

    def _apply_filters(self):
        self._load_parts()

    def _render_table(self, parts: List[SparePart]):
        table = self.table_widget.table
        table.setRowCount(len(parts))

        unit_ar_map = {
            "piece": "قطعة",
            "pieces": "قطعة",
            "unit": "وحدة",
            "units": "وحدات",
            "kit": "طقم",
            "set": "مجموعة",
            "box": "صندوق",
            "roll": "لفة",
            "pack": "حزمة",
            "bottle": "عبوة",
            "pair": "زوج",
            "meter": "متر",
        }

        for row, p in enumerate(parts):
            table.setItem(row, 0, QTableWidgetItem(str(p.id)))
            table.setItem(row, 1, QTableWidgetItem(p.part_number))
            table.setItem(row, 2, QTableWidgetItem(p.name_ar or p.name_en or "—"))
            table.setItem(row, 3, QTableWidgetItem(p.category or "—"))
            table.setItem(row, 4, QTableWidgetItem(p.storage_bin_location or "-"))

            # Unit of measure translated to Arabic cleanly
            raw_u = (p.unit_of_measure or "قطعة").strip()
            unit_ar = unit_ar_map.get(raw_u.lower(), raw_u)
            qty_item = QTableWidgetItem(f"{p.quantity_on_hand:g} {unit_ar}")
            if p.is_low_stock():
                qty_item.setForeground(QColor("#EF4444"))
            table.setItem(row, 5, qty_item)

            table.setItem(row, 6, QTableWidgetItem(f"{p.minimum_reorder_level:g}"))
            table.setItem(row, 7, QTableWidgetItem(f"{p.unit_cost:,.2f} ر.س"))

            for c_idx in range(8):
                it = table.item(row, c_idx)
                if it:
                    it.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            # Actions: Adjust Stock, Edit, Delete
            stock_btn = ActionButton(
                action_type="stock",
                tooltip="تسجيل حركة توريد أو صرف",
                text="حركة مخزنية",
                callback=lambda _, pid=p.id: self._open_stock_dialog(pid)
            )
            edit_btn = ActionButton(
                action_type="edit",
                tooltip="تعديل بيانات القطعة",
                callback=lambda _, pid=p.id: self._open_edit_dialog(pid)
            )
            del_btn = ActionButton(
                action_type="delete",
                tooltip="حذف قطعة الغيار",
                callback=lambda _, pid=p.id: self._delete_part(pid)
            )

            actions_widget = create_actions_cell(stock_btn, edit_btn, del_btn)
            table.setCellWidget(row, 8, actions_widget)

        self.table_widget.set_record_count(len(parts), len(parts))

    def _open_add_dialog(self):
        dlg = SparePartDialog(parent=self)
        if dlg.exec():
            self.refresh_data()

    def _open_edit_dialog(self, part_id: int):
        dlg = SparePartDialog(part_id=part_id, parent=self)
        if dlg.exec():
            self.refresh_data()

    def _open_stock_dialog(self, part_id: int):
        dlg = StockTransactionDialog(part_id=part_id, parent=self)
        if dlg.exec():
            self.refresh_data()

    def _delete_part(self, part_id: int):
        if not confirm_action(self, "تأكيد الحذف", "هل أنت متأكد من حذف صنف قطعة الغيار هذه من المستودع؟"):
            return
        try:
            with get_db() as db:
                inventory_service.delete_spare_part(db, part_id)
            self.refresh_data()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))

    def _on_search(self, query: str):
        query = query.lower().strip()
        if not query:
            self._render_table(self.all_parts)
            return

        filtered = [
            p for p in self.all_parts
            if query in (p.part_number or '').lower()
            or query in (p.name_ar or '').lower()
            or query in (p.name_en or '').lower()
            or query in (p.storage_bin_location or '').lower()
        ]
        self._render_table(filtered)

    def retranslate_ui(self):
        self.refresh_data()
