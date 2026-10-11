"""
staff_dialog.py
---------------
Add / Edit dialog for Staff and Technicians (Phase 3).
"""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Optional

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.exc import IntegrityError

from database import get_session
from models import Department, Staff
from .translations import Translator

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class StaffDialog(QDialog):
    """Modal dialog for creating or editing staff / technician records."""

    def __init__(
        self,
        translator: Translator,
        staff: Optional[Staff] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.t = translator
        self.staff = staff
        self.is_edit = staff is not None

        title_key = "staff.edit_title" if self.is_edit else "staff.add_title"
        self.setWindowTitle(self.t.t(title_key))
        self.setMinimumWidth(520)
        self.setModal(True)

        self._build_ui()
        if self.is_edit:
            self._populate_fields()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(16)

        # Form
        self.form = QFormLayout()
        self.form.setSpacing(12)
        self.form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.staff_id_edit = QLineEdit()
        self.staff_id_edit.setPlaceholderText("EMP-1001")

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(
            "م. أحمد علي" if self.t.lang == "ar" else "Eng. Ahmed Ali"
        )

        self.job_title_combo = QComboBox()
        self.job_title_combo.setEditable(True)
        job_roles = [
            "مهندس أجهزة طبية / Biomedical Engineer",
            "فني صيانة أجهزة طبية / Biomedical Technician",
            "مدير قسم الصيانة / Maintenance Manager",
            "مشغل أجهزة طبية / Equipment Operator",
            "أخصائي نظم ومعلومات طبية / Clinical IT",
            "فني كهرباء وميكانيك طبي / Electro-Mechanical Tech",
        ]
        for role in job_roles:
            self.job_title_combo.addItem(role)

        self.specialty_edit = QLineEdit()
        self.specialty_edit.setPlaceholderText(
            "أشعة ورنين / Radiology" if self.t.lang == "ar" else "Radiology, ICU, Lab..."
        )

        self.dept_combo = QComboBox()
        self._load_departments()

        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("+966 5X XXX XXXX")

        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("technician@hospital.med")

        self.hire_date_edit = QDateEdit()
        self.hire_date_edit.setCalendarPopup(True)
        self.hire_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.hire_date_edit.setDate(QDate.currentDate())

        self.status_combo = QComboBox()
        self.status_combo.addItem(self.t.t("staff.status.active"), "active")
        self.status_combo.addItem(self.t.t("staff.status.inactive"), "inactive")

        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)

        # Add rows to form
        self.form.addRow(self.t.t("staff.field.staff_id"), self.staff_id_edit)
        self.form.addRow(self.t.t("staff.field.name"), self.name_edit)
        self.form.addRow(self.t.t("staff.field.job_title"), self.job_title_combo)
        self.form.addRow(self.t.t("staff.field.specialty"), self.specialty_edit)
        self.form.addRow(self.t.t("staff.field.department"), self.dept_combo)
        self.form.addRow(self.t.t("staff.field.phone"), self.phone_edit)
        self.form.addRow(self.t.t("staff.field.email"), self.email_edit)
        self.form.addRow(self.t.t("staff.field.hire_date"), self.hire_date_edit)
        self.form.addRow(self.t.t("staff.field.status"), self.status_combo)
        self.form.addRow(self.t.t("staff.field.notes"), self.notes_edit)

        layout.addLayout(self.form)

        # Buttons
        btn_box = QDialogButtonBox()
        self.save_btn = btn_box.addButton(
            self.t.t("common.save"), QDialogButtonBox.AcceptRole
        )
        self.cancel_btn = btn_box.addButton(
            self.t.t("common.cancel"), QDialogButtonBox.RejectRole
        )
        self.save_btn.setObjectName("btnPrimary")
        self.cancel_btn.setObjectName("btnSecondary")
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.setCursor(Qt.PointingHandCursor)

        btn_box.accepted.connect(self._validate_and_save)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def _load_departments(self) -> None:
        self.dept_combo.clear()
        self.dept_combo.addItem(self.t.t("common.none"), None)
        try:
            with get_session() as session:
                depts = session.query(Department).order_by(Department.name_ar).all()
                for d in depts:
                    name = d.name_ar if self.t.lang == "ar" else (d.name_en or d.name_ar)
                    self.dept_combo.addItem(f"{d.code} - {name}", d.id)
        except Exception:
            pass

    def _populate_fields(self) -> None:
        if not self.staff:
            return
        self.staff_id_edit.setText(self.staff.staff_id or "")
        self.name_edit.setText(self.staff.full_name or "")
        
        # Set job title
        jt = self.staff.job_title or ""
        idx = self.job_title_combo.findText(jt)
        if idx >= 0:
            self.job_title_combo.setCurrentIndex(idx)
        else:
            self.job_title_combo.setCurrentText(jt)

        self.specialty_edit.setText(self.staff.specialty or "")

        # Department
        if self.staff.department_id:
            dept_idx = self.dept_combo.findData(self.staff.department_id)
            if dept_idx >= 0:
                self.dept_combo.setCurrentIndex(dept_idx)

        self.phone_edit.setText(self.staff.phone or "")
        self.email_edit.setText(self.staff.email or "")

        if self.staff.hire_date:
            try:
                if isinstance(self.staff.hire_date, str):
                    d = datetime.strptime(self.staff.hire_date, "%Y-%m-%d").date()
                else:
                    d = self.staff.hire_date
                self.hire_date_edit.setDate(QDate(d.year, d.month, d.day))
            except Exception:
                pass

        # Status
        status_idx = self.status_combo.findData(self.staff.status)
        if status_idx >= 0:
            self.status_combo.setCurrentIndex(status_idx)

        self.notes_edit.setPlainText(self.staff.notes or "")

    def _validate_and_save(self) -> None:
        staff_id = self.staff_id_edit.text().strip()
        full_name = self.name_edit.text().strip()
        job_title = self.job_title_combo.currentText().strip()
        specialty = self.specialty_edit.text().strip()
        dept_id = self.dept_combo.currentData()
        phone = self.phone_edit.text().strip()
        email = self.email_edit.text().strip()
        qd = self.hire_date_edit.date()
        hire_date_val = date(qd.year(), qd.month(), qd.day())
        status = self.status_combo.currentData() or "active"
        notes = self.notes_edit.toPlainText().strip()

        # Required fields validation
        if not staff_id or not full_name or not job_title:
            QMessageBox.warning(
                self, self.t.t("app.error"), self.t.t("staff.required")
            )
            return

        # Email format check if provided
        if email and not EMAIL_REGEX.match(email):
            QMessageBox.warning(
                self, self.t.t("app.error"), self.t.t("staff.invalid_email")
            )
            return

        # Duplicate staff_id check
        try:
            with get_session() as session:
                query = session.query(Staff).filter(Staff.staff_code == staff_id)
                if self.is_edit and self.staff:
                    query = query.filter(Staff.id != self.staff.id)
                existing = query.first()

                if existing:
                    QMessageBox.warning(
                        self, self.t.t("app.error"), self.t.t("staff.duplicate")
                    )
                    return

                # Save record
                if self.is_edit and self.staff:
                    target = session.query(Staff).filter_by(id=self.staff.id).first()
                    if not target:
                        QMessageBox.critical(self, self.t.t("app.error"), "Record not found.")
                        return
                else:
                    target = Staff()
                    session.add(target)

                target.staff_code = staff_id
                target.full_name = full_name
                target.position = job_title
                target.specialization = specialty or None
                target.department_id = dept_id
                target.phone = phone or None
                target.email = email or None
                target.hire_date = hire_date_val
                target.is_active = (status == "active")
                target.notes = notes or None

                session.commit()
        except IntegrityError:
            QMessageBox.warning(
                self, self.t.t("app.error"), self.t.t("staff.duplicate")
            )
            return
        except Exception as exc:
            QMessageBox.critical(self, self.t.t("app.error"), str(exc))
            return

        self.accept()
