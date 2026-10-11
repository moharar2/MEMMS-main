"""
staff_page.py
-------------
Staff & Technicians Management Page (Phase 3).
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy import or_

from database import get_session
from models import Department, Staff
from .staff_dialog import StaffDialog
from .translations import TranslatableWidget, Translator


class MiniStatCard(QFrame):
    """Modern statistic badge widget for summary numbers."""

    def __init__(self, title: str, value: str = "0", accent_color: str = "#2563eb", parent=None):
        super().__init__(parent)
        self.setObjectName("MiniStatCard")
        self.setStyleSheet(f"""
            #MiniStatCard {{
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-left: 4px solid {accent_color};
                border-radius: 8px;
                padding: 10px 16px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        self.lbl_title = QLabel(title)
        self.lbl_title.setStyleSheet("color: #64748b; font-size: 11.5px; font-weight: 600;")

        self.lbl_val = QLabel(value)
        self.lbl_val.setStyleSheet(f"color: #0f172a; font-size: 18px; font-weight: 700;")

        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_val)

    def set_value(self, val: str) -> None:
        self.lbl_val.setText(str(val))

    def set_title(self, title: str) -> None:
        self.lbl_title.setText(title)


class StaffPage(QWidget, TranslatableWidget):
    """Full-featured Staff & Technicians Management view."""

    def __init__(self, translator: Translator, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.t = translator
        self._build_ui()
        self.retranslate_ui(self.t.lang)
        self.refresh()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 24)
        root.setSpacing(16)

        # Top Header & Actions bar
        header_row = QHBoxLayout()
        header_row.setSpacing(12)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        self.heading = QLabel()
        self.heading.setStyleSheet("font-size: 20px; font-weight: 700; color: #0f172a;")
        self.subtitle = QLabel()
        self.subtitle.setStyleSheet("font-size: 12.5px; color: #64748b;")
        title_box.addWidget(self.heading)
        title_box.addWidget(self.subtitle)
        header_row.addLayout(title_box)

        header_row.addStretch(1)

        # Action buttons
        self.add_btn = QPushButton()
        self.add_btn.setObjectName("btnPrimary")
        self.add_btn.setCursor(Qt.PointingHandCursor)

        self.edit_btn = QPushButton()
        self.edit_btn.setObjectName("btnSecondary")
        self.edit_btn.setCursor(Qt.PointingHandCursor)

        self.delete_btn = QPushButton()
        self.delete_btn.setObjectName("btnDanger")
        self.delete_btn.setCursor(Qt.PointingHandCursor)

        self.reload_btn = QPushButton()
        self.reload_btn.setObjectName("btnSecondary")
        self.reload_btn.setCursor(Qt.PointingHandCursor)

        header_row.addWidget(self.add_btn)
        header_row.addWidget(self.edit_btn)
        header_row.addWidget(self.delete_btn)
        header_row.addWidget(self.reload_btn)

        root.addLayout(header_row)

        # Mini statistics cards row
        self.stats_row = QHBoxLayout()
        self.stats_row.setSpacing(14)
        self.stat_total = MiniStatCard("Total Staff", "0", "#2563eb")
        self.stat_active = MiniStatCard("Active Staff", "0", "#16a34a")
        self.stat_techs = MiniStatCard("Biomedical Techs", "0", "#0891b2")
        self.stat_depts = MiniStatCard("Departments", "0", "#8b5cf6")

        self.stats_row.addWidget(self.stat_total)
        self.stats_row.addWidget(self.stat_active)
        self.stats_row.addWidget(self.stat_techs)
        self.stats_row.addWidget(self.stat_depts)
        root.addLayout(self.stats_row)

        # Filter & Search bar
        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setClearButtonEnabled(True)

        self.dept_filter = QComboBox()
        self.dept_filter.setMinimumWidth(160)

        self.status_filter = QComboBox()
        self.status_filter.setMinimumWidth(130)

        self.reset_filter_btn = QPushButton()
        self.reset_filter_btn.setObjectName("btnSecondary")
        self.reset_filter_btn.setCursor(Qt.PointingHandCursor)

        filter_bar.addWidget(self.search_input, 3)
        filter_bar.addWidget(self.dept_filter, 2)
        filter_bar.addWidget(self.status_filter, 1)
        filter_bar.addWidget(self.reset_filter_btn)

        root.addLayout(filter_bar)

        # Table
        self.table = QTableWidget(0, 8)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

        root.addWidget(self.table, 1)

        # Event connections
        self.search_input.textChanged.connect(self.refresh)
        self.dept_filter.currentIndexChanged.connect(self.refresh)
        self.status_filter.currentIndexChanged.connect(self.refresh)
        self.reset_filter_btn.clicked.connect(self._reset_filters)

        self.add_btn.clicked.connect(self.add_staff)
        self.edit_btn.clicked.connect(self.edit_staff)
        self.delete_btn.clicked.connect(self.delete_staff)
        self.reload_btn.clicked.connect(self.refresh)
        self.table.cellDoubleClicked.connect(lambda row, col: self.edit_staff())

    def _reset_filters(self) -> None:
        self.search_input.clear()
        self.dept_filter.setCurrentIndex(0)
        self.status_filter.setCurrentIndex(0)
        self.refresh()

    def _populate_filter_dropdowns(self) -> None:
        current_dept = self.dept_filter.currentData()
        self.dept_filter.blockSignals(True)
        self.dept_filter.clear()
        self.dept_filter.addItem(self.t.t("staff.filter.all_depts"), None)

        try:
            with get_session() as session:
                depts = session.query(Department).order_by(Department.name_ar).all()
                for d in depts:
                    name = d.name_ar if self.t.lang == "ar" else (d.name_en or d.name_ar)
                    self.dept_filter.addItem(name, d.id)
        except Exception:
            pass

        if current_dept is not None:
            idx = self.dept_filter.findData(current_dept)
            if idx >= 0:
                self.dept_filter.setCurrentIndex(idx)
        self.dept_filter.blockSignals(False)

        current_status = self.status_filter.currentData()
        self.status_filter.blockSignals(True)
        self.status_filter.clear()
        self.status_filter.addItem(self.t.t("staff.filter.all_statuses"), None)
        self.status_filter.addItem(self.t.t("staff.status.active"), "active")
        self.status_filter.addItem(self.t.t("staff.status.inactive"), "inactive")

        if current_status is not None:
            idx = self.status_filter.findData(current_status)
            if idx >= 0:
                self.status_filter.setCurrentIndex(idx)
        self.status_filter.blockSignals(False)

    def retranslate_ui(self, lang: str) -> None:
        self.heading.setText(self.t.t("staff.heading"))
        self.subtitle.setText(self.t.t("staff.subtitle"))
        self.search_input.setPlaceholderText(self.t.t("staff.search"))

        self.add_btn.setText(self.t.t("staff.add"))
        self.edit_btn.setText(self.t.t("staff.edit"))
        self.delete_btn.setText(self.t.t("staff.delete"))
        self.reload_btn.setText(self.t.t("app.refresh"))
        self.reset_filter_btn.setText(self.t.t("staff.filter.reset"))

        self.stat_total.set_title(self.t.t("staff.stats.total"))
        self.stat_active.set_title(self.t.t("staff.stats.active"))
        self.stat_techs.set_title(self.t.t("staff.stats.technicians"))
        self.stat_depts.set_title(self.t.t("equipment.col.department"))

        headers = [
            self.t.t("staff.col.staff_id"),
            self.t.t("staff.col.name"),
            self.t.t("staff.col.job_title"),
            self.t.t("staff.col.specialty"),
            self.t.t("staff.col.department"),
            self.t.t("staff.col.phone"),
            self.t.t("staff.col.email"),
            self.t.t("staff.col.status"),
        ]
        self.table.setHorizontalHeaderLabels(headers)
        self._populate_filter_dropdowns()

    def refresh(self) -> None:
        query_text = self.search_input.text().strip()
        dept_id = self.dept_filter.currentData()
        status_val = self.status_filter.currentData()

        try:
            with get_session() as session:
                # Update mini statistics
                total_count = session.query(Staff).count()
                active_count = session.query(Staff).filter(Staff.is_active == True).count()
                tech_count = session.query(Staff).filter(
                    or_(
                        Staff.position.ilike("%مهندس%"),
                        Staff.position.ilike("%فني%"),
                        Staff.position.ilike("%engineer%"),
                        Staff.position.ilike("%tech%"),
                    )
                ).count()
                dept_count = session.query(Department).count()

                self.stat_total.set_value(str(total_count))
                self.stat_active.set_value(str(active_count))
                self.stat_techs.set_value(str(tech_count))
                self.stat_depts.set_value(str(dept_count))

                # Main list query
                query = session.query(Staff)

                if dept_id:
                    query = query.filter(Staff.department_id == dept_id)

                if status_val:
                    is_act = (status_val == "active")
                    query = query.filter(Staff.is_active == is_act)

                if query_text:
                    term = f"%{query_text}%"
                    query = query.filter(
                        or_(
                            Staff.staff_code.ilike(term),
                            Staff.full_name.ilike(term),
                            Staff.position.ilike(term),
                            Staff.specialization.ilike(term),
                            Staff.phone.ilike(term),
                            Staff.email.ilike(term),
                        )
                    )

                staff_list = query.order_by(Staff.staff_code.asc()).all()

                self.table.setRowCount(len(staff_list))
                for row_idx, item in enumerate(staff_list):
                    # Staff ID
                    id_item = QTableWidgetItem(item.staff_id or "")
                    id_item.setData(Qt.UserRole, item.id)
                    id_item.setFont(QFont("Segoe UI", 9, QFont.Bold))
                    self.table.setItem(row_idx, 0, id_item)

                    # Full name
                    name_item = QTableWidgetItem(item.full_name or "")
                    self.table.setItem(row_idx, 1, name_item)

                    # Job title
                    job_item = QTableWidgetItem(item.job_title or "")
                    self.table.setItem(row_idx, 2, job_item)

                    # Specialty
                    spec_item = QTableWidgetItem(item.specialty or "—")
                    self.table.setItem(row_idx, 3, spec_item)

                    # Department
                    dept_name = "—"
                    if item.department:
                        dept_name = (
                            item.department.name_ar
                            if self.t.lang == "ar"
                            else (item.department.name_en or item.department.name_ar)
                        )
                    dept_item = QTableWidgetItem(dept_name)
                    self.table.setItem(row_idx, 4, dept_item)

                    # Phone
                    phone_item = QTableWidgetItem(item.phone or "—")
                    self.table.setItem(row_idx, 5, phone_item)

                    # Email
                    email_item = QTableWidgetItem(item.email or "—")
                    self.table.setItem(row_idx, 6, email_item)

                    # Status badge
                    is_active = item.status == "active"
                    status_text = self.t.t("staff.status.active" if is_active else "staff.status.inactive")
                    status_item = QTableWidgetItem(status_text)
                    if is_active:
                        status_item.setForeground(QColor("#16a34a"))
                    else:
                        status_item.setForeground(QColor("#dc2626"))
                    status_item.setFont(QFont("Segoe UI", 9, QFont.Bold))
                    self.table.setItem(row_idx, 7, status_item)

        except Exception as exc:
            QMessageBox.critical(self, self.t.t("app.error"), str(exc))

    def _get_selected_staff_id(self) -> Optional[int]:
        selected = self.table.currentRow()
        if selected < 0:
            return None
        item = self.table.item(selected, 0)
        return item.data(Qt.UserRole) if item else None

    def add_staff(self) -> None:
        dlg = StaffDialog(self.t, parent=self)
        if dlg.exec():
            self.refresh()

    def edit_staff(self) -> None:
        staff_pk = self._get_selected_staff_id()
        if not staff_pk:
            QMessageBox.information(
                self, self.t.t("app.title"), self.t.t("staff.select")
            )
            return

        try:
            with get_session() as session:
                staff_obj = session.query(Staff).filter_by(id=staff_pk).first()
                if not staff_obj:
                    return
                dlg = StaffDialog(self.t, staff=staff_obj, parent=self)
                if dlg.exec():
                    self.refresh()
        except Exception as exc:
            QMessageBox.critical(self, self.t.t("app.error"), str(exc))

    def delete_staff(self) -> None:
        staff_pk = self._get_selected_staff_id()
        if not staff_pk:
            QMessageBox.information(
                self, self.t.t("app.title"), self.t.t("staff.select")
            )
            return

        confirm = QMessageBox.question(
            self,
            self.t.t("staff.delete"),
            self.t.t("staff.confirm_delete"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return

        try:
            with get_session() as session:
                staff_obj = session.query(Staff).filter_by(id=staff_pk).first()
                if staff_obj:
                    session.delete(staff_obj)
                    session.commit()
            self.refresh()
        except Exception as exc:
            QMessageBox.critical(
                self, self.t.t("app.error"), f"{self.t.t('staff.delete_blocked')}\n{exc}"
            )
