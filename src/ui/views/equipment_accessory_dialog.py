"""
Dialog for adding and editing Medical Equipment Accessories.
Pure Arabic, RTL, zero emojis, automatic cost calculation.
"""
from typing import Optional, Dict, Any
from datetime import date
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QDoubleSpinBox, QTextEdit, QPushButton, QMessageBox, QFrame
)
from PySide6.QtCore import Qt
from src.core.i18n import tr
from src.models.equipment import EquipmentAccessory
from src.ui.theme.icons import icon


class EquipmentAccessoryDialog(QDialog):
    def __init__(self, accessory: Optional[EquipmentAccessory] = None, parent=None):
        super().__init__(parent)
        self.accessory = accessory
        action_title = "تعديل ملحق الجهاز" if accessory else "إضافة ملحق جديد للجهاز"
        self.setWindowTitle(f"{action_title} — MEMMS")
        self.setFixedSize(520, 420)
        self.setModal(True)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(14)

        # Header
        header = QFrame()
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(0, 0, 0, 4)
        h_layout.setSpacing(10)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(icon("inventory", color="#0F766E", size=22).pixmap(22, 22))
        title_lbl = QLabel(action_title)
        title_lbl.setStyleSheet("font-size: 16px; font-weight: 700; color: #0F172A;")

        h_layout.addWidget(icon_lbl)
        h_layout.addWidget(title_lbl)
        h_layout.addStretch()
        layout.addWidget(header)

        # Form
        grid = QGridLayout()
        grid.setSpacing(10)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("مثال: مجس استشعار حراري، بطارية احتياطية...")
        self.model_input = QLineEdit()
        self.serial_input = QLineEdit()
        self.manufacturer_input = QLineEdit()

        self.qty_input = QDoubleSpinBox()
        self.qty_input.setRange(1.0, 9999.0)
        self.qty_input.setDecimals(0)
        self.qty_input.setValue(1.0)
        self.qty_input.valueChanged.connect(self._recalc_total)

        self.unit_cost_input = QDoubleSpinBox()
        self.unit_cost_input.setRange(0.0, 1000000.0)
        self.unit_cost_input.setDecimals(2)
        self.unit_cost_input.setSuffix(" ر.س")
        self.unit_cost_input.setValue(0.0)
        self.unit_cost_input.valueChanged.connect(self._recalc_total)

        self.total_cost_lbl = QLabel("0.00 ر.س")
        self.total_cost_lbl.setStyleSheet("font-size: 14px; font-weight: 800; color: #0F766E;")

        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(65)
        self.notes_input.setPlaceholderText("ملاحظات إضافية...")

        grid.addWidget(QLabel("اسم الملحق *:"), 0, 0)
        grid.addWidget(self.name_input, 0, 1, 1, 2)

        grid.addWidget(QLabel("رقم الموديل:"), 1, 0)
        grid.addWidget(self.model_input, 1, 1, 1, 2)

        grid.addWidget(QLabel("الرقم التسلسلي:"), 2, 0)
        grid.addWidget(self.serial_input, 2, 1, 1, 2)

        grid.addWidget(QLabel("الشركة المصنعة:"), 3, 0)
        grid.addWidget(self.manufacturer_input, 3, 1, 1, 2)

        grid.addWidget(QLabel("الكمية *:"), 4, 0)
        grid.addWidget(self.qty_input, 4, 1)

        grid.addWidget(QLabel("تكلفة الوحدة:"), 5, 0)
        grid.addWidget(self.unit_cost_input, 5, 1)

        grid.addWidget(QLabel("إجمالي التكلفة:"), 6, 0)
        grid.addWidget(self.total_cost_lbl, 6, 1)

        grid.addWidget(QLabel("ملاحظات:"), 7, 0)
        grid.addWidget(self.notes_input, 7, 1, 1, 2)

        layout.addLayout(grid)
        layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.addStretch()

        cancel_btn = QPushButton("إلغاء")
        cancel_btn.setProperty("variant", "secondary")
        cancel_btn.setIcon(icon("cancel", color="#64748B", size=14))
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("حفظ")
        save_btn.setObjectName("primaryBtn")
        save_btn.setIcon(icon("save", color="#FFFFFF", size=14))
        save_btn.clicked.connect(self._save)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

        if self.accessory:
            self._load_data()

    def _recalc_total(self):
        total = self.qty_input.value() * self.unit_cost_input.value()
        self.total_cost_lbl.setText(f"{total:,.2f} ر.س")

    def _load_data(self):
        self.name_input.setText(self.accessory.name or "")
        self.model_input.setText(self.accessory.model_number or "")
        self.serial_input.setText(self.accessory.serial_number or "")
        self.manufacturer_input.setText(self.accessory.manufacturer or "")
        self.qty_input.setValue(float(self.accessory.quantity or 1.0))
        self.unit_cost_input.setValue(float(self.accessory.unit_cost or 0.0))
        self.notes_input.setPlainText(self.accessory.notes or "")
        self._recalc_total()

    def _save(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "خطأ في البيانات", "يرجى كتابة اسم الملحق.")
            return

        self.result_data = {
            "name": name,
            "model_number": self.model_input.text().strip() or None,
            "serial_number": self.serial_input.text().strip() or None,
            "manufacturer": self.manufacturer_input.text().strip() or None,
            "quantity": self.qty_input.value(),
            "unit_cost": self.unit_cost_input.value(),
            "notes": self.notes_input.toPlainText().strip() or None
        }
        self.accept()

    def get_data(self) -> Dict[str, Any]:
        return getattr(self, "result_data", {})
