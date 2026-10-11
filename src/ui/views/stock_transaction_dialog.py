"""
Inventory Stock Transaction Dialog.
Record stock additions, consumption in work orders, and physical inventory reconciliations.
Pure Arabic, RTL, zero emojis.
"""
from typing import Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QComboBox, QDoubleSpinBox, QTextEdit, QPushButton,
    QFrame, QMessageBox
)
from src.core.i18n import tr
from src.core.database import get_db
from src.models.inventory import SparePart
from src.models.work_order import WorkOrder
from src.services.inventory_service import inventory_service
from src.ui.theme.icons import icon


class StockTransactionDialog(QDialog):
    def __init__(self, part_id: int, parent=None):
        super().__init__(parent)
        self.part_id = part_id
        self.setWindowTitle("حركة مخزنية لقطعة الغيار")
        self.resize(540, 440)
        self.setMinimumSize(480, 390)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(16)

        # Header
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 6)
        header_layout.setSpacing(12)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(icon("stock", color="#0F766E", size=24).pixmap(24, 24))

        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        dlg_title = QLabel("تسجيل حركة مخزنية")
        dlg_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #0F172A;")
        self.sub_lbl = QLabel()
        self.sub_lbl.setStyleSheet("font-size: 12px; color: #64748B;")
        title_layout.addWidget(dlg_title)
        title_layout.addWidget(self.sub_lbl)

        header_layout.addWidget(icon_lbl)
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        main_layout.addWidget(header_frame)

        # Grid
        grid = QGridLayout()
        grid.setSpacing(12)

        # Current stock info
        grid.addWidget(QLabel("الرصيد الحالي المتوفر:"), 0, 0)
        self.curr_balance_lbl = QLabel("0.0")
        self.curr_balance_lbl.setStyleSheet("font-weight: 700; color: #0F766E; font-size: 14px;")
        grid.addWidget(self.curr_balance_lbl, 0, 1)

        # Transaction type
        grid.addWidget(QLabel("نوع الحركة المخزنية *"), 1, 0)
        self.type_combo = QComboBox()
        self.type_combo.addItem("إضافة مخزنية (شراء وتوريد)", "in_purchase")
        self.type_combo.addItem("مرتجع إلى المستودع", "in_return")
        self.type_combo.addItem("صرف لأمر صيانة", "out_work_order")
        self.type_combo.addItem("تسوية جردية", "adjustment")
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        grid.addWidget(self.type_combo, 1, 1)

        # Quantity
        grid.addWidget(QLabel("الكمية *"), 2, 0)
        self.qty_spin = QDoubleSpinBox()
        self.qty_spin.setRange(0.1, 99999.0)
        self.qty_spin.setValue(1.0)
        grid.addWidget(self.qty_spin, 2, 1)

        # Unit cost
        grid.addWidget(QLabel("تكلفة الوحدة (ر.س)"), 3, 0)
        self.cost_spin = QDoubleSpinBox()
        self.cost_spin.setRange(0.0, 999999.0)
        self.cost_spin.setDecimals(2)
        grid.addWidget(self.cost_spin, 3, 1)

        # Work order association (optional)
        self.wo_lbl = QLabel("أمر الصيانة المرتبط:")
        self.wo_combo = QComboBox()
        self.wo_combo.addItem("-- غير محدد --", None)
        grid.addWidget(self.wo_lbl, 4, 0)
        grid.addWidget(self.wo_combo, 4, 1)

        # Reference / Invoice / PO
        grid.addWidget(QLabel("رقم المرجع / الفاتورة / أمر الشراء"), 5, 0)
        self.ref_edit = QLineEdit()
        self.ref_edit.setPlaceholderText("مثال: فاتورة توريد #1042 أو أمر شراء PO-2026")
        grid.addWidget(self.ref_edit, 5, 1)

        main_layout.addLayout(grid)

        # Notes
        main_layout.addWidget(QLabel("ملاحظات إضافية"))
        self.notes_edit = QTextEdit()
        self.notes_edit.setFixedHeight(50)
        main_layout.addWidget(self.notes_edit)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("إلغاء")
        cancel_btn.setIcon(icon("cancel", color="#64748B", size=14))
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("تأكيد الحركة")
        save_btn.setObjectName("primaryBtn")
        save_btn.setIcon(icon("save", color="#FFFFFF", size=14))
        save_btn.clicked.connect(self._on_save)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        main_layout.addLayout(btn_layout)

        self._load_part_info()

    def _load_part_info(self):
        with get_db() as db:
            part = db.query(SparePart).filter(SparePart.id == self.part_id).first()
            if not part:
                self.reject()
                return

            p_name = part.name_ar or part.name_en or "قطعة غيار"
            self.sub_lbl.setText(f"{part.part_number} — {p_name}")
            self.curr_balance_lbl.setText(f"{part.quantity_on_hand:g} {part.unit_of_measure or 'قطعة'}")
            self.cost_spin.setValue(part.unit_cost or 0.0)

            # Load active work orders
            wos = db.query(WorkOrder).filter(WorkOrder.status.in_(["open", "pending", "assigned", "in_progress", "waiting_parts"])).all()
            for wo in wos:
                desc = wo.failure_description[:25] if wo.failure_description else "صيانة"
                self.wo_combo.addItem(f"أمر صيانة #{wo.work_order_number} ({desc})", wo.id)

    def _on_type_changed(self):
        tx_type = self.type_combo.currentData()
        is_wo = (tx_type == "out_work_order")
        self.wo_lbl.setVisible(is_wo)
        self.wo_combo.setVisible(is_wo)

    def _on_save(self):
        tx_type = self.type_combo.currentData()
        qty = self.qty_spin.value()
        cost = self.cost_spin.value()
        wo_id = self.wo_combo.currentData() if tx_type == "out_work_order" else None
        ref = self.ref_edit.text().strip() or None
        notes = self.notes_edit.toPlainText().strip() or None

        try:
            with get_db() as db:
                inventory_service.record_transaction(
                    db,
                    part_id=self.part_id,
                    transaction_type=tx_type,
                    quantity=qty,
                    unit_cost=cost,
                    work_order_id=wo_id,
                    reference_number=ref,
                    notes=notes
                )

            QMessageBox.information(self, "تم بنجاح", "تم تسجيل الحركة المخزنية وتحديث رصيد القطعة بنجاح.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))
