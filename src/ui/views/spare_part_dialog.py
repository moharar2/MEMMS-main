"""
Spare Part Add/Edit Dialog.
Enterprise 2-column form for biomedical spare parts catalog. Pure Arabic, RTL, zero emojis.
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
from src.models.vendor import Vendor
from src.services.inventory_service import inventory_service
from src.ui.theme.icons import icon


class SparePartDialog(QDialog):
    def __init__(self, part_id: Optional[int] = None, parent=None):
        super().__init__(parent)
        self.part_id = part_id
        self.setWindowTitle("إضافة قطعة غيار جديدة" if not part_id else "تعديل بيانات قطعة الغيار")
        self.resize(620, 500)
        self.setMinimumSize(540, 440)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(16)

        # Header banner
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 6)
        header_layout.setSpacing(12)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(icon("inventory", color="#0F766E", size=24).pixmap(24, 24))

        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        dlg_title = QLabel("إضافة قطعة غيار جديدة" if not part_id else "تعديل بيانات قطعة الغيار")
        dlg_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #0F172A;")
        dlg_sub = QLabel("بيانات بطاقة الصنف والمورد ومستويات إعادة الطلب والتسعير")
        dlg_sub.setStyleSheet("font-size: 12px; color: #64748B;")
        title_layout.addWidget(dlg_title)
        title_layout.addWidget(dlg_sub)

        header_layout.addWidget(icon_lbl)
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        main_layout.addWidget(header_frame)

        # Form Grid
        grid = QGridLayout()
        grid.setSpacing(12)

        # Part Number & Category
        grid.addWidget(QLabel("رقم القطعة / الكود *"), 0, 0)
        self.part_no_edit = QLineEdit()
        self.part_no_edit.setPlaceholderText("مثال: FLT-HEPA-99")
        grid.addWidget(self.part_no_edit, 0, 1)

        grid.addWidget(QLabel("التصنيف *"), 0, 2)
        self.cat_combo = QComboBox()
        self.cat_combo.setEditable(True)
        self.cat_combo.addItems([
            "فلاتر وأغشية طبية", "بطاريات ووحدات طاقة", "مجسات وحساسات (Sensors & Probes)",
            "كابلات وأسلاك توصيل", "صمامات وأنابيب طبية", "محركات وأجزاء ميكانيكية", "مصابيح وألياف بصرية", "مستهلكات طبية"
        ])
        grid.addWidget(self.cat_combo, 0, 3)

        # Names: Ar & En
        grid.addWidget(QLabel("اسم القطعة (بالعربية) *"), 1, 0)
        self.name_ar_edit = QLineEdit()
        self.name_ar_edit.setPlaceholderText("مثال: فلتر سحب هواء عالي الكفاءة HEPA")
        grid.addWidget(self.name_ar_edit, 1, 1)

        grid.addWidget(QLabel("الاسم (بالإنجليزية)"), 1, 2)
        self.name_en_edit = QLineEdit()
        self.name_en_edit.setPlaceholderText("e.g., HEPA Intake Filter")
        grid.addWidget(self.name_en_edit, 1, 3)

        # Storage Bin & Unit of measure
        grid.addWidget(QLabel("موقع التخزين (الرف/الخانة)"), 2, 0)
        self.bin_edit = QLineEdit()
        self.bin_edit.setPlaceholderText("مثال: رف B-04")
        grid.addWidget(self.bin_edit, 2, 1)

        grid.addWidget(QLabel("وحدة القياس"), 2, 2)
        self.uom_combo = QComboBox()
        self.uom_combo.addItems(["قطعة", "طقم / مجموعة", "صندوق", "متر", "لفة", "عبوة"])
        grid.addWidget(self.uom_combo, 2, 3)

        # Quantities and Costs
        grid.addWidget(QLabel("الرصيد الافتتاحي"), 3, 0)
        self.qty_spin = QDoubleSpinBox()
        self.qty_spin.setRange(0.0, 999999.0)
        self.qty_spin.setDecimals(1)
        grid.addWidget(self.qty_spin, 3, 1)

        grid.addWidget(QLabel("حد إعادة الطلب (الأمان)"), 3, 2)
        self.reorder_spin = QDoubleSpinBox()
        self.reorder_spin.setRange(0.0, 99999.0)
        self.reorder_spin.setValue(5.0)
        grid.addWidget(self.reorder_spin, 3, 3)

        grid.addWidget(QLabel("تكلفة الوحدة (ر.س)"), 4, 0)
        self.cost_spin = QDoubleSpinBox()
        self.cost_spin.setRange(0.0, 999999.0)
        self.cost_spin.setDecimals(2)
        self.cost_spin.setSuffix(" ر.س")
        grid.addWidget(self.cost_spin, 4, 1)

        grid.addWidget(QLabel("المورد / الشركة المصنعة"), 4, 2)
        self.vendor_combo = QComboBox()
        self.vendor_combo.addItem("-- غير محدد --", None)
        grid.addWidget(self.vendor_combo, 4, 3)

        main_layout.addLayout(grid)

        # Description
        main_layout.addWidget(QLabel("الوصف والمواصفات الفنية"))
        self.desc_edit = QTextEdit()
        self.desc_edit.setFixedHeight(60)
        main_layout.addWidget(self.desc_edit)

        # Actions
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("إلغاء")
        cancel_btn.setIcon(icon("cancel", color="#64748B", size=14))
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("حفظ")
        save_btn.setObjectName("primaryBtn")
        save_btn.setIcon(icon("save", color="#FFFFFF", size=14))
        save_btn.clicked.connect(self._on_save)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        main_layout.addLayout(btn_layout)

        self._load_vendors()
        if self.part_id:
            self._load_part()

    def _load_vendors(self):
        with get_db() as db:
            vendors = db.query(Vendor).order_by(Vendor.name.asc()).all()
            for v in vendors:
                self.vendor_combo.addItem(v.name, v.id)

    def _load_part(self):
        with get_db() as db:
            part = db.query(SparePart).filter(SparePart.id == self.part_id).first()
            if not part:
                return
            self.part_no_edit.setText(part.part_number)
            self.name_ar_edit.setText(part.name_ar or "")
            self.name_en_edit.setText(part.name_en or "")
            self.bin_edit.setText(part.storage_bin_location or "")
            self.qty_spin.setValue(part.quantity_on_hand)
            self.reorder_spin.setValue(part.minimum_reorder_level)
            self.cost_spin.setValue(part.unit_cost)
            self.desc_edit.setText(part.description or "")

            idx = self.cat_combo.findText(part.category)
            if idx >= 0:
                self.cat_combo.setCurrentIndex(idx)
            else:
                self.cat_combo.setCurrentText(part.category)

            uom_idx = self.uom_combo.findText(part.unit_of_measure)
            if uom_idx >= 0:
                self.uom_combo.setCurrentIndex(uom_idx)

            if part.manufacturer_id:
                v_idx = self.vendor_combo.findData(part.manufacturer_id)
                if v_idx >= 0:
                    self.vendor_combo.setCurrentIndex(v_idx)

    def _on_save(self):
        part_no = self.part_no_edit.text().strip()
        name_ar = self.name_ar_edit.text().strip()
        name_en = self.name_en_edit.text().strip()
        cat = self.cat_combo.currentText().strip()

        if not part_no or not (name_ar or name_en) or not cat:
            QMessageBox.warning(self, "خطأ في البيانات", "يرجى تعبئة الحقول الإلزامية المطلوبة (رقم القطعة، الاسم، التصنيف).")
            return

        try:
            with get_db() as db:
                if self.part_id:
                    inventory_service.update_spare_part(
                        db,
                        self.part_id,
                        part_number=part_no,
                        name_en=name_en or name_ar,
                        name_ar=name_ar or name_en,
                        category=cat,
                        storage_bin_location=self.bin_edit.text().strip() or None,
                        quantity_on_hand=self.qty_spin.value(),
                        minimum_reorder_level=self.reorder_spin.value(),
                        unit_cost=self.cost_spin.value(),
                        unit_of_measure=self.uom_combo.currentText(),
                        manufacturer_id=self.vendor_combo.currentData(),
                        description=self.desc_edit.toPlainText().strip() or None
                    )
                else:
                    inventory_service.create_spare_part(
                        db,
                        part_number=part_no,
                        name_en=name_en or name_ar,
                        name_ar=name_ar or name_en,
                        category=cat,
                        storage_bin_location=self.bin_edit.text().strip() or None,
                        quantity_on_hand=self.qty_spin.value(),
                        minimum_reorder_level=self.reorder_spin.value(),
                        unit_cost=self.cost_spin.value(),
                        unit_of_measure=self.uom_combo.currentText(),
                        manufacturer_id=self.vendor_combo.currentData(),
                        description=self.desc_edit.toPlainText().strip() or None
                    )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))
