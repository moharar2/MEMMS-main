"""
Departments and Locations View: List, manage, and create hospital departments and rooms.
Pure Arabic, RTL, zero emojis.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidgetItem, QMessageBox, QLabel, QFrame, QHeaderView
)
from PySide6.QtCore import Qt
from src.core.i18n import tr
from src.core.database import get_db
from src.services.hospital_service import hospital_service
from src.services.auth_service import auth_service
from src.ui.theme.icons import icon
from src.ui.components.data_table import DataTable
from src.ui.components.confirm_dialog import confirm_action
from src.ui.components.action_button import ActionButton, create_actions_cell
from src.ui.views.department_dialog import DepartmentDialog


class DepartmentsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(10)

        # Header Frame
        header_frame = QFrame()
        h_layout = QHBoxLayout(header_frame)
        h_layout.setContentsMargins(0, 0, 0, 0)

        titles_box = QVBoxLayout()
        titles_box.setSpacing(2)
        self.title_lbl = QLabel("الأقسام الطبية والمواقع")
        self.title_lbl.setStyleSheet("font-size: 16px; font-weight: 800; color: #0F172A;")

        self.subtitle_lbl = QLabel("إدارة الهيكل التنظيمي وأقسام المستشفى وتوزيع الأجهزة الطبية")
        self.subtitle_lbl.setStyleSheet("font-size: 11px; color: #64748B; font-weight: 500;")

        titles_box.addWidget(self.title_lbl)
        titles_box.addWidget(self.subtitle_lbl)
        h_layout.addLayout(titles_box)
        h_layout.addStretch()

        layout.addWidget(header_frame)

        headers = [
            "كود القسم",
            "اسم القسم (بالعربية)",
            "اسم القسم (بالإنجليزية)",
            "الدور / الطابق",
            "عدد الأجهزة المرتبطة",
            "الإجراءات"
        ]

        self.table_widget = DataTable()
        self.table_widget.set_search_placeholder("بحث بكود القسم أو الاسم...")
        self.table_widget.set_headers(headers)
        self.table_widget.set_add_button_text("+ إضافة قسم")
        self.table_widget.search_changed.connect(lambda txt: self.load_data())
        self.table_widget.refresh_requested.connect(self.load_data)
        self.table_widget.add_clicked.connect(self._on_add)
        # 0: Code, 1: Name AR, 2: Name EN, 3: Floor, 4: Equip Count, 5: Actions
        self.table_widget.set_column_widths([100, 200, 180, 100, 120, 90], stretch_cols=[1, 2])
        self.table_widget.table.verticalHeader().setDefaultSectionSize(38)

        layout.addWidget(self.table_widget, stretch=1)
        self.load_data()

    def load_data(self):
        search_txt = self.table_widget.search_input.text().strip().lower()

        with get_db() as db:
            hospital_service.get_or_create_default_hospital(db)
            depts = hospital_service.get_departments(db)

            if search_txt:
                depts = [
                    d for d in depts
                    if search_txt in d.name_ar.lower()
                    or search_txt in (d.name_en or "").lower()
                    or search_txt in d.code.lower()
                ]

            tbl = self.table_widget.table
            tbl.setRowCount(len(depts))

            for row_idx, dept in enumerate(depts):
                it_code = QTableWidgetItem(dept.code)
                it_code.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                tbl.setItem(row_idx, 0, it_code)

                it_ar = QTableWidgetItem(dept.name_ar)
                it_ar.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                tbl.setItem(row_idx, 1, it_ar)

                it_en = QTableWidgetItem(dept.name_en or "—")
                it_en.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                tbl.setItem(row_idx, 2, it_en)

                it_fl = QTableWidgetItem(dept.floor or "—")
                it_fl.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                tbl.setItem(row_idx, 3, it_fl)

                it_cnt = QTableWidgetItem(str(len(dept.equipment)))
                it_cnt.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                tbl.setItem(row_idx, 4, it_cnt)

                # Action buttons (Edit, Delete)
                edit_btn = ActionButton(
                    action_type="edit",
                    tooltip="تعديل بيانات القسم",
                    callback=lambda _, d_id=dept.id: self._on_edit(d_id)
                )
                del_btn = ActionButton(
                    action_type="delete",
                    tooltip="حذف القسم",
                    callback=lambda _, d_id=dept.id: self._on_delete(d_id)
                )

                actions_widget = create_actions_cell(edit_btn, del_btn)
                tbl.setCellWidget(row_idx, 5, actions_widget)

            self.table_widget.set_record_count(len(depts), len(depts))

    def _on_add(self):
        dlg = DepartmentDialog(parent=self)
        if dlg.exec() == DepartmentDialog.DialogCode.Accepted:
            self.load_data()

    def _on_edit(self, dept_id: int):
        with get_db() as db:
            dept = hospital_service.get_department_by_id(db, dept_id)
            if not dept:
                return
            dlg = DepartmentDialog(department=dept, parent=self)
            if dlg.exec() == DepartmentDialog.DialogCode.Accepted:
                self.load_data()

    def _on_delete(self, dept_id: int):
        if confirm_action(self, "تأكيد الحذف", "هل أنت متأكد من رغبتك في حذف هذا القسم الطبي؟"):
            user = auth_service.current_user
            try:
                with get_db() as db:
                    hospital_service.delete_department(db, user, dept_id)
                self.load_data()
            except Exception as e:
                QMessageBox.critical(self, "خطأ", str(e))

    def retranslate_ui(self):
        self.load_data()
