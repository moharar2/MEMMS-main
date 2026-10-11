"""
Dialog for creating and editing vendors, manufacturers, and agents.
Pure Arabic, RTL, zero emojis.
"""
from typing import Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QComboBox, QTextEdit, QPushButton, QMessageBox, QLabel
)
from src.core.database import get_db
from src.services.vendor_service import vendor_service
from src.services.auth_service import auth_service
from src.models.vendor import Vendor
from src.ui.theme.icons import icon


class VendorDialog(QDialog):
    def __init__(self, vendor: Optional[Vendor] = None, parent=None):
        super().__init__(parent)
        self.vendor = vendor
        action_title = "تعديل بيانات الشركة" if vendor else "إضافة مورد / شركة جديدة"
        self.setWindowTitle(f"{action_title} — نظام إدارة الصيانة الطبية")
        self.setFixedSize(540, 480)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(14)

        title_lbl = QLabel(action_title)
        title_lbl.setStyleSheet("font-size: 16px; font-weight: 700; color: #0F172A;")
        layout.addWidget(title_lbl)

        form = QFormLayout()
        form.setSpacing(10)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("مثال: شركة جنرال إلكتريك للرعاية الصحية")

        self.type_combo = QComboBox()
        self.type_combo.addItem("مورد وموزع معتمد", "supplier")
        self.type_combo.addItem("شركة مصنعة", "manufacturer")
        self.type_combo.addItem("وكيل صيانة وخدمة", "service_agent")
        self.type_combo.addItem("مصنع ومورد شامل", "both")

        self.contact_person_input = QLineEdit()
        self.contact_person_input.setPlaceholderText("اسم المهندس / مسؤول التواصل")

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("مثال: +966 11 000 0000")

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("مثال: contact@vendor.com")

        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("العنوان والمدينة")

        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(70)
        self.notes_input.setPlaceholderText("ملاحظات إضافية، عقود سابقة...")

        form.addRow("اسم الشركة / المورد *:", self.name_input)
        form.addRow("نوع النشاط / التصنيف:", self.type_combo)
        form.addRow("الشخص المسؤول:", self.contact_person_input)
        form.addRow("رقم الهاتف:", self.phone_input)
        form.addRow("البريد الإلكتروني:", self.email_input)
        form.addRow("العنوان:", self.address_input)
        form.addRow("ملاحظات:", self.notes_input)

        layout.addLayout(form)
        layout.addStretch()

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        if self.vendor:
            eng_btn = QPushButton("مهندسو الدعم الفني")
            eng_btn.setIcon(icon("technicians", color="#0F766E", size=14))
            eng_btn.setStyleSheet("""
                QPushButton {
                    background-color: #F0FDFA;
                    color: #0F766E;
                    font-weight: 600;
                    font-size: 11px;
                    padding: 6px 12px;
                    border: 1px solid #99F6E4;
                    border-radius: 6px;
                }
                QPushButton:hover { background-color: #CCFBF1; }
            """)
            eng_btn.clicked.connect(self._open_engineers_dialog)
            btn_layout.addWidget(eng_btn)

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

        if self.vendor:
            self._load_data()

    def _load_data(self):
        self.name_input.setText(self.vendor.name or "")
        idx = self.type_combo.findData(self.vendor.vendor_type)
        if idx >= 0:
            self.type_combo.setCurrentIndex(idx)
        self.contact_person_input.setText(self.vendor.contact_person or "")
        self.phone_input.setText(self.vendor.phone or "")
        self.email_input.setText(self.vendor.email or "")
        self.address_input.setText(self.vendor.address or "")
        self.notes_input.setPlainText(self.vendor.notes or "")

    def _save(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "خطأ في البيانات", "يرجى كتابة اسم الشركة أو المورد.")
            return

        user = auth_service.current_user
        data = {
            "name": name,
            "vendor_type": self.type_combo.currentData(),
            "contact_person": self.contact_person_input.text().strip() or None,
            "phone": self.phone_input.text().strip() or None,
            "email": self.email_input.text().strip() or None,
            "address": self.address_input.text().strip() or None,
            "notes": self.notes_input.toPlainText().strip() or None
        }

        try:
            with get_db() as db:
                if self.vendor:
                    vendor_service.update_vendor(db, user, self.vendor.id, data)
                else:
                    vendor_service.create_vendor(db, user, data)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))

    def _open_engineers_dialog(self):
        if not self.vendor:
            return
        from src.ui.views.vendor_engineers_dialog import VendorEngineersDialog
        with get_db() as db:
            fresh_v = vendor_service.get_vendor_by_id(db, self.vendor.id)
            if fresh_v:
                dlg = VendorEngineersDialog(vendor=fresh_v, parent=self)
                dlg.exec()
