"""
Contract & Warranty Add/Edit Dialog.
Enterprise 2-column form for service level agreements, warranties, and supplier contracts.
Pure Arabic, RTL, zero emojis.
"""
from typing import Optional
from datetime import date
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QComboBox, QDoubleSpinBox, QTextEdit, QPushButton,
    QFrame, QMessageBox, QDateEdit
)
from PySide6.QtCore import QDate
from src.core.i18n import tr
from src.core.database import get_db
from src.models.contract import Contract
from src.models.vendor import Vendor
from src.services.contract_service import contract_service
from src.ui.theme.icons import icon


class ContractDialog(QDialog):
    def __init__(self, contract_id: Optional[int] = None, parent=None):
        super().__init__(parent)
        self.contract_id = contract_id
        action_title = "تعديل بيانات العقد" if contract_id else "إضافة عقد صيانة / ضمان جديد"
        self.setWindowTitle(f"{action_title} — نظام إدارة الصيانة الطبية")
        self.resize(640, 520)
        self.setMinimumSize(560, 460)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(16)

        # Header
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 6)
        header_layout.setSpacing(12)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(icon("contracts", color="#0F766E", size=24).pixmap(24, 24))

        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        dlg_title = QLabel(action_title)
        dlg_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #0F172A;")
        dlg_sub = QLabel("توثيق عقود الصيانة السنوية وضمان الوكيل المعتمد وشروط مستوى الخدمة")
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

        # Contract Number & Vendor
        grid.addWidget(QLabel("رقم العقد / المرجع *"), 0, 0)
        self.contract_no_edit = QLineEdit()
        self.contract_no_edit.setPlaceholderText("مثال: SLA-2026-008")
        grid.addWidget(self.contract_no_edit, 0, 1)

        grid.addWidget(QLabel("الشركة / المورد *"), 0, 2)
        self.vendor_combo = QComboBox()
        grid.addWidget(self.vendor_combo, 0, 3)

        # Title & Type
        grid.addWidget(QLabel("عنوان / موضوع العقد *"), 1, 0)
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("مثال: عقد الصيانة الشاملة لأجهزة الرنين المغناطيسي والأشعة المقطعية")
        grid.addWidget(self.title_edit, 1, 1, 1, 3)

        grid.addWidget(QLabel("نوع العقد *"), 2, 0)
        self.type_combo = QComboBox()
        self.type_combo.addItem("عقد صيانة شامل", "comprehensive")
        self.type_combo.addItem("عقد صيانة وقائية وقطع غيار", "preventive_parts")
        self.type_combo.addItem("عقد صيانة وقائية فقط", "preventive_only")
        self.type_combo.addItem("عقد توريد قطع غيار فقط", "parts_only")
        self.type_combo.addItem("عقد ضمان الشركة المصنعة", "warranty")
        self.type_combo.addItem("عقد توريد وخدمة", "supply_service")
        grid.addWidget(self.type_combo, 2, 1)

        grid.addWidget(QLabel("القيمة المالية (ر.س)"), 2, 2)
        self.cost_spin = QDoubleSpinBox()
        self.cost_spin.setRange(0.0, 99999999.0)
        self.cost_spin.setDecimals(2)
        self.cost_spin.setSuffix(" ر.س")
        grid.addWidget(self.cost_spin, 2, 3)

        # Dates
        grid.addWidget(QLabel("تاريخ سريان العقد *"), 3, 0)
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate())
        grid.addWidget(self.start_date_edit, 3, 1)

        grid.addWidget(QLabel("تاريخ انتهاء العقد *"), 3, 2)
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate().addYears(1))
        grid.addWidget(self.end_date_edit, 3, 3)

        main_layout.addLayout(grid)

        # Terms & Scope
        main_layout.addWidget(QLabel("الشروط ومستوى الخدمة وملاحظات التغطية"))
        self.terms_edit = QTextEdit()
        self.terms_edit.setFixedHeight(75)
        self.terms_edit.setPlaceholderText("اكتب شروط الاستجابة، عدد الزيارات الوقائية، وتفاصيل التغطية لقطع الغيار...")
        main_layout.addWidget(self.terms_edit)

        # Buttons
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
        if self.contract_id:
            self._load_contract()

    def _load_vendors(self):
        with get_db() as db:
            vendors = db.query(Vendor).order_by(Vendor.name.asc()).all()
            for v in vendors:
                self.vendor_combo.addItem(v.name, v.id)

    def _load_contract(self):
        with get_db() as db:
            c = db.query(Contract).filter(Contract.id == self.contract_id).first()
            if not c:
                return
            self.contract_no_edit.setText(c.contract_number)
            self.title_edit.setText(c.title)
            self.cost_spin.setValue(c.cost or 0.0)
            self.terms_edit.setText(c.terms or "")

            if c.start_date:
                self.start_date_edit.setDate(QDate(c.start_date.year, c.start_date.month, c.start_date.day))
            if c.end_date:
                self.end_date_edit.setDate(QDate(c.end_date.year, c.end_date.month, c.end_date.day))

            if c.vendor_id:
                v_idx = self.vendor_combo.findData(c.vendor_id)
                if v_idx >= 0:
                    self.vendor_combo.setCurrentIndex(v_idx)

            idx = self.type_combo.findData(c.contract_type)
            if idx >= 0:
                self.type_combo.setCurrentIndex(idx)

    def _on_save(self):
        c_num = self.contract_no_edit.text().strip()
        title = self.title_edit.text().strip()
        vendor_id = self.vendor_combo.currentData()

        if not c_num or not title or not vendor_id:
            QMessageBox.warning(self, "خطأ في البيانات", "يرجى تعبئة الحقول الإلزامية (رقم العقد، العنوان، والشركة الموردة).")
            return

        s_qdate = self.start_date_edit.date()
        e_qdate = self.end_date_edit.date()
        s_date = date(s_qdate.year(), s_qdate.month(), s_qdate.day())
        e_date = date(e_qdate.year(), e_qdate.month(), e_qdate.day())

        try:
            with get_db() as db:
                if self.contract_id:
                    contract_service.update_contract(
                        db,
                        self.contract_id,
                        contract_number=c_num,
                        title=title,
                        vendor_id=vendor_id,
                        contract_type=self.type_combo.currentData(),
                        start_date=s_date,
                        end_date=e_date,
                        cost=self.cost_spin.value(),
                        terms=self.terms_edit.toPlainText().strip() or None
                    )
                else:
                    contract_service.create_contract(
                        db,
                        contract_number=c_num,
                        title=title,
                        vendor_id=vendor_id,
                        contract_type=self.type_combo.currentData(),
                        start_date=s_date,
                        end_date=e_date,
                        cost=self.cost_spin.value(),
                        terms=self.terms_edit.toPlainText().strip() or None
                    )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))
