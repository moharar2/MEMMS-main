"""
Dialog for creating and editing hospital departments.
Pure Arabic, RTL, zero emojis.
"""
from typing import Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QLabel, QMessageBox
)
from src.core.database import get_db
from src.services.hospital_service import hospital_service
from src.services.auth_service import auth_service
from src.models.hospital import Department
from src.ui.theme.icons import icon


class DepartmentDialog(QDialog):
    def __init__(self, department: Optional[Department] = None, parent=None):
        super().__init__(parent)
        self.department = department
        action_title = "تعديل بيانات القسم الطبي" if department else "إضافة قسم طبي جديد"
        self.setWindowTitle(f"{action_title} — نظام إدارة الصيانة الطبية")
        self.setFixedSize(480, 320)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(16)

        title_lbl = QLabel(action_title)
        title_lbl.setStyleSheet("font-size: 16px; font-weight: 700; color: #0F172A;")
        layout.addWidget(title_lbl)

        form = QFormLayout()
        form.setSpacing(12)

        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("مثال: ICU, RAD, CARD, SURG")
        self.name_ar_input = QLineEdit()
        self.name_ar_input.setPlaceholderText("مثال: العناية المركزة، قسم الأشعة")
        self.name_en_input = QLineEdit()
        self.name_en_input.setPlaceholderText("e.g., Intensive Care Unit")
        self.floor_input = QLineEdit()
        self.floor_input.setPlaceholderText("مثال: الطابق الثاني - الجناح الشرقي")

        form.addRow("كود القسم *:", self.code_input)
        form.addRow("اسم القسم (بالعربية) *:", self.name_ar_input)
        form.addRow("الاسم (بالإنجليزية):", self.name_en_input)
        form.addRow("الدور / الطابق:", self.floor_input)

        layout.addLayout(form)
        layout.addStretch()

        # Action Buttons
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

        if self.department:
            self._load_data()

    def _load_data(self):
        self.code_input.setText(self.department.code or "")
        self.name_ar_input.setText(self.department.name_ar or "")
        self.name_en_input.setText(self.department.name_en or "")
        self.floor_input.setText(self.department.floor or "")

    def _save(self):
        code = self.code_input.text().strip()
        name_ar = self.name_ar_input.text().strip()
        if not code or not name_ar:
            QMessageBox.warning(self, "خطأ في البيانات", "يرجى إدخال كود القسم واسم القسم بالعربية.")
            return

        user = auth_service.current_user
        data = {
            "code": code,
            "name_ar": name_ar,
            "name_en": self.name_en_input.text().strip() or name_ar,
            "floor": self.floor_input.text().strip()
        }

        try:
            with get_db() as db:
                if self.department:
                    hospital_service.update_department(db, user, self.department.id, data)
                else:
                    hospital_service.create_department(db, user, data)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))
