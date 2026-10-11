"""
Dialog for recording and editing Medical Equipment Receiving and Commissioning Data.
Pure Arabic, RTL, zero emojis.
"""
from typing import Optional, Dict, Any
from datetime import date
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QDateEdit, QTextEdit, QComboBox, QPushButton, QMessageBox, QFrame
)
from PySide6.QtCore import Qt, QDate
from src.core.database import get_db
from src.models.equipment import EquipmentReceiving
from src.models.technician import Technician
from src.models.user import User
from src.ui.theme.icons import icon


class EquipmentReceivingDialog(QDialog):
    def __init__(self, receiving: Optional[EquipmentReceiving] = None, parent=None):
        super().__init__(parent)
        self.receiving = receiving
        self.setWindowTitle("بيانات الاستلام والتعميد — MEMMS")
        self.setFixedSize(580, 520)
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
        icon_lbl.setPixmap(icon("equipment", color="#0F766E", size=22).pixmap(22, 22))
        title_lbl = QLabel("تسجيل وتعديل بيانات الاستلام والتعميد")
        title_lbl.setStyleSheet("font-size: 16px; font-weight: 700; color: #0F172A;")

        h_layout.addWidget(icon_lbl)
        h_layout.addWidget(title_lbl)
        h_layout.addStretch()
        layout.addWidget(header)

        # Form
        grid = QGridLayout()
        grid.setSpacing(10)

        self.comm_no_input = QLineEdit()
        self.comm_no_input.setPlaceholderText("مثال: COMM-2026-088")

        self.comm_date_input = QDateEdit()
        self.comm_date_input.setCalendarPopup(True)
        self.comm_date_input.setDate(QDate.currentDate())

        self.receipt_date_input = QDateEdit()
        self.receipt_date_input.setCalendarPopup(True)
        self.receipt_date_input.setDate(QDate.currentDate())

        self.receiving_tech_combo = QComboBox()
        self.receiving_tech_combo.setEditable(True)

        self.reg_officer_combo = QComboBox()
        self.reg_officer_combo.setEditable(True)

        self.reg_date_input = QDateEdit()
        self.reg_date_input.setCalendarPopup(True)
        self.reg_date_input.setDate(QDate.currentDate())

        self.report_no_input = QLineEdit()
        self.report_no_input.setPlaceholderText("مثال: REC-REP-102")

        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(70)
        self.notes_input.setPlaceholderText("ملاحظات فنية عن حالة الاستلام، اكتمال المرفقات...")

        self._populate_dropdowns()

        grid.addWidget(QLabel("رقم التعميد:"), 0, 0)
        grid.addWidget(self.comm_no_input, 0, 1)

        grid.addWidget(QLabel("تاريخ التعميد:"), 1, 0)
        grid.addWidget(self.comm_date_input, 1, 1)

        grid.addWidget(QLabel("تاريخ استلام الجهاز:"), 2, 0)
        grid.addWidget(self.receipt_date_input, 2, 1)

        grid.addWidget(QLabel("فني الاستلام المسؤول:"), 3, 0)
        grid.addWidget(self.receiving_tech_combo, 3, 1)

        grid.addWidget(QLabel("مسؤول تسجيل الجهاز:"), 4, 0)
        grid.addWidget(self.reg_officer_combo, 4, 1)

        grid.addWidget(QLabel("تاريخ التسجيل:"), 5, 0)
        grid.addWidget(self.reg_date_input, 5, 1)

        grid.addWidget(QLabel("رقم محضر الاستلام:"), 6, 0)
        grid.addWidget(self.report_no_input, 6, 1)

        grid.addWidget(QLabel("ملاحظات الاستلام:"), 7, 0)
        grid.addWidget(self.notes_input, 7, 1)

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

        save_btn = QPushButton("حفظ بيانات الاستلام")
        save_btn.setObjectName("primaryBtn")
        save_btn.setIcon(icon("save", color="#FFFFFF", size=14))
        save_btn.clicked.connect(self._save)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

        if self.receiving:
            self._load_data()

    def _populate_dropdowns(self):
        with get_db() as db:
            techs = db.query(Technician).filter_by(status="active").order_by(Technician.full_name.asc()).all()
            self.receiving_tech_combo.addItem("— اختر فني الاستلام —", None)
            for t in techs:
                self.receiving_tech_combo.addItem(f"{t.full_name} ({t.specialization})", t.id)

            users = db.query(User).filter_by(is_active=True).order_by(User.full_name.asc()).all()
            self.reg_officer_combo.addItem("— اختر مسؤول التسجيل —", None)
            for u in users:
                self.reg_officer_combo.addItem(f"{u.full_name or u.username}", u.id)

    def _load_data(self):
        self.comm_no_input.setText(self.receiving.commissioning_number or "")
        if self.receiving.commissioning_date:
            d = self.receiving.commissioning_date
            self.comm_date_input.setDate(QDate(d.year, d.month, d.day))
        if self.receiving.receipt_date:
            d = self.receiving.receipt_date
            self.receipt_date_input.setDate(QDate(d.year, d.month, d.day))
        if self.receiving.registration_date:
            d = self.receiving.registration_date
            self.reg_date_input.setDate(QDate(d.year, d.month, d.day))

        t_idx = self.receiving_tech_combo.findData(self.receiving.receiving_technician_id)
        if t_idx >= 0:
            self.receiving_tech_combo.setCurrentIndex(t_idx)
        elif self.receiving.receiving_technician_name:
            self.receiving_tech_combo.setCurrentText(self.receiving.receiving_technician_name)

        u_idx = self.reg_officer_combo.findData(self.receiving.registration_officer_id)
        if u_idx >= 0:
            self.reg_officer_combo.setCurrentIndex(u_idx)
        elif self.receiving.registration_officer_name:
            self.reg_officer_combo.setCurrentText(self.receiving.registration_officer_name)

        self.report_no_input.setText(self.receiving.receipt_report_number or "")
        self.notes_input.setPlainText(self.receiving.receipt_notes or "")

    def _save(self):
        c_date = self.comm_date_input.date().toPython()
        r_date = self.receipt_date_input.date().toPython()
        reg_date = self.reg_date_input.date().toPython()

        tech_id = self.receiving_tech_combo.currentData()
        tech_name = self.receiving_tech_combo.currentText() if not tech_id else self.receiving_tech_combo.currentText().split(" (")[0]
        if tech_name.startswith("—"):
            tech_name = None

        officer_id = self.reg_officer_combo.currentData()
        officer_name = self.reg_officer_combo.currentText()
        if officer_name.startswith("—"):
            officer_name = None

        self.result_data = {
            "commissioning_number": self.comm_no_input.text().strip() or None,
            "commissioning_date": c_date,
            "receipt_date": r_date,
            "receiving_technician_id": tech_id,
            "receiving_technician_name": tech_name,
            "registration_officer_id": officer_id,
            "registration_officer_name": officer_name,
            "registration_date": reg_date,
            "receipt_report_number": self.report_no_input.text().strip() or None,
            "receipt_notes": self.notes_input.toPlainText().strip() or None
        }
        self.accept()

    def get_data(self) -> Dict[str, Any]:
        return getattr(self, "result_data", {})
