"""
Technician / Clinical Engineer Add & Edit Dialog.
Enterprise form for biomedical engineering staff with full personal data,
qualifications, professional experiences, and RBAC-protected compensation.
Pure Arabic, RTL, zero emojis.
"""
from typing import Optional, Dict, Any
from datetime import date
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QComboBox, QPushButton, QFrame, QMessageBox,
    QTabWidget, QWidget, QDateEdit, QDoubleSpinBox, QTextEdit,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt, QDate
from src.core.i18n import tr
from src.core.database import get_db
from src.models.technician import (
    Technician, TechnicianQualification,
    TechnicianExperience, TechnicianCompensation
)
from src.models.hospital import Department
from src.services.technician_service import technician_service
from src.services.auth_service import auth_service
from src.core.permissions import (
    can_user, PERM_TECHNICIANS_SALARY_VIEW, PERM_TECHNICIANS_SALARY_MANAGE
)
from src.ui.theme.icons import icon


class QualificationFormDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("إضافة مؤهل علمي / شهادة مهنية — MEMMS")
        self.setFixedSize(480, 360)
        self.setModal(True)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        grid = QGridLayout()
        grid.setSpacing(10)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("مثال: بكالوريوس هندسة طبية حيوية، شهادة صيانة أجهزة تخدير...")
        self.spec_input = QLineEdit()
        self.org_input = QLineEdit()
        self.org_input.setPlaceholderText("الجامعة، الهيئة، أو الشركة المانحة")

        self.issue_date = QDateEdit()
        self.issue_date.setCalendarPopup(True)
        self.issue_date.setDate(QDate.currentDate())

        self.expiry_date = QDateEdit()
        self.expiry_date.setCalendarPopup(True)
        self.expiry_date.setDate(QDate.currentDate().addYears(3))

        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(60)

        grid.addWidget(QLabel("اسم المؤهل / الشهادة *:"), 0, 0)
        grid.addWidget(self.name_input, 0, 1)

        grid.addWidget(QLabel("التخصص:"), 1, 0)
        grid.addWidget(self.spec_input, 1, 1)

        grid.addWidget(QLabel("الجهة المانحة:"), 2, 0)
        grid.addWidget(self.org_input, 2, 1)

        grid.addWidget(QLabel("تاريخ الحصول عليها:"), 3, 0)
        grid.addWidget(self.issue_date, 3, 1)

        grid.addWidget(QLabel("تاريخ الانتهاء (إن وجد):"), 4, 0)
        grid.addWidget(self.expiry_date, 4, 1)

        grid.addWidget(QLabel("ملاحظات:"), 5, 0)
        grid.addWidget(self.notes_input, 5, 1)

        layout.addLayout(grid)
        layout.addStretch()

        btn_box = QHBoxLayout()
        btn_box.addStretch()
        c_btn = QPushButton("إلغاء")
        c_btn.clicked.connect(self.reject)
        s_btn = QPushButton("إضافة المؤهل")
        s_btn.setObjectName("primaryBtn")
        s_btn.clicked.connect(self._save)
        btn_box.addWidget(c_btn)
        btn_box.addWidget(s_btn)
        layout.addLayout(btn_box)

    def _save(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "خطأ", "اسم المؤهل أو الشهادة مطلوب.")
            return

        self.result_data = {
            "name": name,
            "specialization": self.spec_input.text().strip() or None,
            "issuing_organization": self.org_input.text().strip() or None,
            "issue_date": self.issue_date.date().toPython(),
            "expiry_date": self.expiry_date.date().toPython(),
            "notes": self.notes_input.toPlainText().strip() or None
        }
        self.accept()


class ExperienceFormDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("إضافة خبرة مهنية سابقة — MEMMS")
        self.setFixedSize(500, 400)
        self.setModal(True)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        grid = QGridLayout()
        grid.setSpacing(10)

        self.employer_input = QLineEdit()
        self.employer_input.setPlaceholderText("مثال: مستشفى التخصصي، شركة سيمنز...")
        self.job_title_input = QLineEdit()
        self.job_title_input.setPlaceholderText("مثال: مهندس صيانة أجهزة أشعة")
        self.spec_input = QLineEdit()

        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addYears(-2))

        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())

        self.tasks_input = QTextEdit()
        self.tasks_input.setMaximumHeight(70)
        self.tasks_input.setPlaceholderText("وصف المهام والأنظمة الطبية التي تمت صيانتها...")

        grid.addWidget(QLabel("جهة العمل السابقة *:"), 0, 0)
        grid.addWidget(self.employer_input, 0, 1)

        grid.addWidget(QLabel("المسمى الوظيفي *:"), 1, 0)
        grid.addWidget(self.job_title_input, 1, 1)

        grid.addWidget(QLabel("التخصص:"), 2, 0)
        grid.addWidget(self.spec_input, 2, 1)

        grid.addWidget(QLabel("تاريخ البداية *:"), 3, 0)
        grid.addWidget(self.start_date, 3, 1)

        grid.addWidget(QLabel("تاريخ النهاية:"), 4, 0)
        grid.addWidget(self.end_date, 4, 1)

        grid.addWidget(QLabel("وصف المهام:"), 5, 0)
        grid.addWidget(self.tasks_input, 5, 1)

        layout.addLayout(grid)
        layout.addStretch()

        btn_box = QHBoxLayout()
        btn_box.addStretch()
        c_btn = QPushButton("إلغاء")
        c_btn.clicked.connect(self.reject)
        s_btn = QPushButton("إضافة الخبرة")
        s_btn.setObjectName("primaryBtn")
        s_btn.clicked.connect(self._save)
        btn_box.addWidget(c_btn)
        btn_box.addWidget(s_btn)
        layout.addLayout(btn_box)

    def _save(self):
        employer = self.employer_input.text().strip()
        title = self.job_title_input.text().strip()
        if not employer or not title:
            QMessageBox.warning(self, "خطأ", "جهة العمل والمسمى الوظيفي حقول إلزامية.")
            return

        self.result_data = {
            "previous_employer": employer,
            "job_title": title,
            "specialization": self.spec_input.text().strip() or None,
            "start_date": self.start_date.date().toPython(),
            "end_date": self.end_date.date().toPython(),
            "task_description": self.tasks_input.toPlainText().strip() or None
        }
        self.accept()


class TechnicianDialog(QDialog):
    def __init__(self, tech_id: Optional[int] = None, parent=None):
        super().__init__(parent)
        self.tech_id = tech_id
        action_title = "تعديل ملف الموظف / المهندس" if tech_id else "إضافة مهندس / فني صيانة جديد"
        self.setWindowTitle(f"{action_title} — نظام إدارة الصيانة الطبية")
        self.resize(780, 580)
        self.setMinimumSize(700, 500)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(12)

        # Header
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 4)
        header_layout.setSpacing(12)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(icon("technicians", color="#0F766E", size=24).pixmap(24, 24))

        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        dlg_title = QLabel(action_title)
        dlg_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #0F172A;")
        dlg_sub = QLabel("السجل المهني والإداري الشامل والمؤهلات والبيانات المالية")
        dlg_sub.setStyleSheet("font-size: 12px; color: #64748B;")
        title_layout.addWidget(dlg_title)
        title_layout.addWidget(dlg_sub)

        header_layout.addWidget(icon_lbl)
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        main_layout.addWidget(header_frame)

        # Tabs
        self.tabs = QTabWidget()

        # Tab 1: Personal & Administrative Data
        self._build_personal_tab()

        # Tab 2: Qualifications & Certificates
        self._build_qualifications_tab()

        # Tab 3: Professional Experiences
        self._build_experiences_tab()

        # Tab 4: Salary & Allowances
        self._build_compensation_tab()

        main_layout.addWidget(self.tabs, stretch=1)

        # Actions Bar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("إلغاء")
        cancel_btn.setIcon(icon("cancel", color="#64748B", size=14))
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("حفظ التغييرات")
        save_btn.setObjectName("primaryBtn")
        save_btn.setIcon(icon("save", color="#FFFFFF", size=14))
        save_btn.clicked.connect(self._on_save_all)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        main_layout.addLayout(btn_layout)

        if self.tech_id:
            self._load_tech_data()

    def _build_personal_tab(self):
        tab = QWidget()
        grid = QGridLayout(tab)
        grid.setContentsMargins(16, 16, 16, 16)
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(12)

        self.emp_id_edit = QLineEdit()
        self.emp_id_edit.setPlaceholderText("مثال: BME-102")

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("مثال: م. أحمد الرشيدي")

        self.job_title_edit = QLineEdit()
        self.job_title_edit.setPlaceholderText("مثال: مهندس أجهزة طبية أول")

        self.spec_combo = QComboBox()
        self.spec_combo.setEditable(True)
        self.spec_combo.addItems([
            "الهندسة الطبية الحيوية (عام)",
            "أجهزة الأشعة والتصوير الطبي",
            "أجهزة العناية المركزة والتنفس الصناعي",
            "أجهزة المختبرات والتحاليل الطبية",
            "الأجهزة الجراحية وغرف العمليات",
            "أجهزة القلب والأوعية الدموية والقسطرة",
            "أجهزة غسيل الكلى والكلى الصناعية",
            "المعايرة والسلامة الكهربائية الطبية"
        ])

        self.nationality_edit = QLineEdit()
        self.nationality_edit.setPlaceholderText("مثال: سعودي، مصري، أردني...")

        self.id_type_combo = QComboBox()
        self.id_type_combo.addItem("هوية وطنية", "national_id")
        self.id_type_combo.addItem("إقامة", "iqama")
        self.id_type_combo.addItem("جواز سفر", "passport")

        self.id_num_edit = QLineEdit()
        self.id_num_edit.setPlaceholderText("رقم الهوية أو الإقامة...")

        self.dept_combo = QComboBox()
        self._populate_departments()

        self.work_entity_edit = QLineEdit()
        self.work_entity_edit.setPlaceholderText("مثال: مستشفى الملك فهد، شركة الصيانة المشغلة...")

        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("+966 50 000 0000")

        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("engineer@hospital.com")

        self.hire_date_edit = QDateEdit()
        self.hire_date_edit.setCalendarPopup(True)
        self.hire_date_edit.setDate(QDate.currentDate())

        self.status_combo = QComboBox()
        self.status_combo.addItem("على رأس العمل (نشط)", "active")
        self.status_combo.addItem("في إجازة", "on_leave")
        self.status_combo.addItem("غير نشط / منتهي الخدمة", "inactive")

        grid.addWidget(QLabel("الرقم الوظيفي *:"), 0, 0)
        grid.addWidget(self.emp_id_edit, 0, 1)
        grid.addWidget(QLabel("الاسم الكامل *:"), 0, 2)
        grid.addWidget(self.name_edit, 0, 3)

        grid.addWidget(QLabel("المسمى الوظيفي:"), 1, 0)
        grid.addWidget(self.job_title_edit, 1, 1)
        grid.addWidget(QLabel("التخصص الهندسي *:"), 1, 2)
        grid.addWidget(self.spec_combo, 1, 3)

        grid.addWidget(QLabel("الجنسية:"), 2, 0)
        grid.addWidget(self.nationality_edit, 2, 1)
        grid.addWidget(QLabel("نوع وثيقة الهوية:"), 2, 2)
        grid.addWidget(self.id_type_combo, 2, 3)

        grid.addWidget(QLabel("رقم الهوية / الإقامة:"), 3, 0)
        grid.addWidget(self.id_num_edit, 3, 1)
        grid.addWidget(QLabel("القسم التابع له:"), 3, 2)
        grid.addWidget(self.dept_combo, 3, 3)

        grid.addWidget(QLabel("جهة العمل / المشغل:"), 4, 0)
        grid.addWidget(self.work_entity_edit, 4, 1)
        grid.addWidget(QLabel("تاريخ التعيين:"), 4, 2)
        grid.addWidget(self.hire_date_edit, 4, 3)

        grid.addWidget(QLabel("رقم الهاتف:"), 5, 0)
        grid.addWidget(self.phone_edit, 5, 1)
        grid.addWidget(QLabel("البريد الإلكتروني:"), 5, 2)
        grid.addWidget(self.email_edit, 5, 3)

        grid.addWidget(QLabel("الحالة الوظيفية:"), 6, 0)
        grid.addWidget(self.status_combo, 6, 1)

        self.tabs.addTab(tab, "البيانات الشخصية والإدارية")

    def _populate_departments(self):
        with get_db() as db:
            depts = db.query(Department).order_by(Department.name_ar.asc()).all()
            self.dept_combo.addItem("— غير محدد —", None)
            for d in depts:
                self.dept_combo.addItem(d.name_ar, d.id)

    def _build_qualifications_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        bar = QHBoxLayout()
        add_btn = QPushButton("+ إضافة مؤهل أو شهادة")
        add_btn.setObjectName("primaryBtn")
        add_btn.setIcon(icon("add", color="#FFFFFF", size=14))
        add_btn.clicked.connect(self._add_qualification)
        bar.addWidget(add_btn)

        del_btn = QPushButton("حذف المؤهل")
        del_btn.setIcon(icon("delete", color="#DC2626", size=14))
        del_btn.clicked.connect(self._delete_qualification)
        bar.addWidget(del_btn)
        bar.addStretch()
        layout.addLayout(bar)

        self.qual_table = QTableWidget()
        self.qual_table.setColumnCount(5)
        self.qual_table.setHorizontalHeaderLabels([
            "اسم المؤهل / الشهادة",
            "التخصص",
            "الجهة المانحة",
            "تاريخ الحصول عليها",
            "تاريخ الانتهاء"
        ])
        self.qual_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.qual_table.verticalHeader().setVisible(False)
        self.qual_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.qual_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.qual_table.setAlternatingRowColors(True)

        layout.addWidget(self.qual_table)
        self.tabs.addTab(tab, "المؤهلات والشهادات")

    def _refresh_qualifications(self):
        if not self.tech_id:
            return
        with get_db() as db:
            quals = technician_service.get_qualifications(db, self.tech_id)
            self.cached_quals = quals
            self.qual_table.setRowCount(len(quals))
            for i, q in enumerate(quals):
                self.qual_table.setItem(i, 0, QTableWidgetItem(q.name))
                self.qual_table.setItem(i, 1, QTableWidgetItem(q.specialization or "—"))
                self.qual_table.setItem(i, 2, QTableWidgetItem(q.issuing_organization or "—"))
                self.qual_table.setItem(i, 3, QTableWidgetItem(str(q.issue_date or "—")))
                self.qual_table.setItem(i, 4, QTableWidgetItem(str(q.expiry_date or "سارية / دائم")))

    def _add_qualification(self):
        if not self.tech_id:
            QMessageBox.information(self, "تنبيه", "يرجى حفظ البيانات الأساسية أولاً لتتمكن من ربط الشهادات.")
            return
        dlg = QualificationFormDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            user = auth_service.current_user
            with get_db() as db:
                technician_service.add_qualification(db, user, self.tech_id, dlg.result_data)
            self._refresh_qualifications()

    def _delete_qualification(self):
        row = self.qual_table.currentRow()
        if not hasattr(self, "cached_quals") or not (0 <= row < len(self.cached_quals)):
            QMessageBox.information(self, "تنبيه", "يرجى اختيار مؤهل للحذف.")
            return
        qual = self.cached_quals[row]
        ans = QMessageBox.question(self, "تأكيد الحذف", f"هل أنت متأكد من حذف المؤهل '{qual.name}'؟")
        if ans == QMessageBox.StandardButton.Yes:
            user = auth_service.current_user
            with get_db() as db:
                technician_service.delete_qualification(db, user, qual.id)
            self._refresh_qualifications()

    def _build_experiences_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        bar = QHBoxLayout()
        add_btn = QPushButton("+ إضافة خبرة سابقة")
        add_btn.setObjectName("primaryBtn")
        add_btn.setIcon(icon("add", color="#FFFFFF", size=14))
        add_btn.clicked.connect(self._add_experience)
        bar.addWidget(add_btn)

        del_btn = QPushButton("حذف الخبرة")
        del_btn.setIcon(icon("delete", color="#DC2626", size=14))
        del_btn.clicked.connect(self._delete_experience)
        bar.addWidget(del_btn)
        bar.addStretch()
        layout.addLayout(bar)

        self.exp_table = QTableWidget()
        self.exp_table.setColumnCount(6)
        self.exp_table.setHorizontalHeaderLabels([
            "جهة العمل السابقة",
            "المسمى الوظيفي",
            "التخصص",
            "من تاريخ",
            "إلى تاريخ",
            "سنوات الخبرة"
        ])
        self.exp_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.exp_table.verticalHeader().setVisible(False)
        self.exp_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.exp_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.exp_table.setAlternatingRowColors(True)

        layout.addWidget(self.exp_table)
        self.tabs.addTab(tab, "الخبرات المهنية")

    def _refresh_experiences(self):
        if not self.tech_id:
            return
        with get_db() as db:
            exps = technician_service.get_experiences(db, self.tech_id)
            self.cached_exps = exps
            self.exp_table.setRowCount(len(exps))
            for i, exp in enumerate(exps):
                self.exp_table.setItem(i, 0, QTableWidgetItem(exp.previous_employer))
                self.exp_table.setItem(i, 1, QTableWidgetItem(exp.job_title))
                self.exp_table.setItem(i, 2, QTableWidgetItem(exp.specialization or "—"))
                self.exp_table.setItem(i, 3, QTableWidgetItem(str(exp.start_date)))
                self.exp_table.setItem(i, 4, QTableWidgetItem(str(exp.end_date or "مستمر")))
                self.exp_table.setItem(i, 5, QTableWidgetItem(f"{exp.calculated_years:.1f} سنة"))

    def _add_experience(self):
        if not self.tech_id:
            QMessageBox.information(self, "تنبيه", "يرجى حفظ البيانات الأساسية أولاً لتتمكن من إضافة الخبرات.")
            return
        dlg = ExperienceFormDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            user = auth_service.current_user
            with get_db() as db:
                technician_service.add_experience(db, user, self.tech_id, dlg.result_data)
            self._refresh_experiences()

    def _delete_experience(self):
        row = self.exp_table.currentRow()
        if not hasattr(self, "cached_exps") or not (0 <= row < len(self.cached_exps)):
            QMessageBox.information(self, "تنبيه", "يرجى اختيار خبرة للحذف.")
            return
        exp = self.cached_exps[row]
        ans = QMessageBox.question(self, "تأكيد الحذف", f"هل أنت متأكد من حذف الخبرة لدى '{exp.previous_employer}'؟")
        if ans == QMessageBox.StandardButton.Yes:
            user = auth_service.current_user
            with get_db() as db:
                technician_service.delete_experience(db, user, exp.id)
            self._refresh_experiences()

    def _build_compensation_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        user = auth_service.current_user
        has_perm = can_user(user, PERM_TECHNICIANS_SALARY_VIEW)

        if not has_perm:
            lock_frame = QFrame()
            lock_frame.setStyleSheet("background-color: #FEF2F2; border: 1px solid #FCA5A5; border-radius: 8px; padding: 24px;")
            l_box = QVBoxLayout(lock_frame)
            l_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl = QLabel("عذراً، لا تملك الصلاحية للاطلاع على البيانات المالية والرواتب لهذا الموظف.")
            lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #991B1B;")
            l_box.addWidget(lbl)
            layout.addWidget(lock_frame)
            layout.addStretch()
            self.tabs.addTab(tab, "البيانات المالية والرواتب")
            return

        # Authorized view
        grid = QGridLayout()
        grid.setSpacing(12)

        self.basic_salary_input = QDoubleSpinBox()
        self.basic_salary_input.setRange(0.0, 1000000.0)
        self.basic_salary_input.setDecimals(2)
        self.basic_salary_input.setSuffix(" ر.س")
        self.basic_salary_input.valueChanged.connect(self._recalc_total_comp)

        self.allowances_input = QDoubleSpinBox()
        self.allowances_input.setRange(0.0, 1000000.0)
        self.allowances_input.setDecimals(2)
        self.allowances_input.setSuffix(" ر.س")
        self.allowances_input.valueChanged.connect(self._recalc_total_comp)

        self.allowance_type_edit = QLineEdit()
        self.allowance_type_edit.setPlaceholderText("مثال: بدل سكن وبدل نقل وبدل ندرة")

        self.total_package_lbl = QLabel("0.00 ر.س")
        self.total_package_lbl.setStyleSheet("font-size: 15px; font-weight: 800; color: #0F766E;")

        self.comp_effective_date = QDateEdit()
        self.comp_effective_date.setCalendarPopup(True)
        self.comp_effective_date.setDate(QDate.currentDate())

        self.comp_notes_edit = QTextEdit()
        self.comp_notes_edit.setMaximumHeight(65)
        self.comp_notes_edit.setPlaceholderText("ملاحظات إضافية عن السلم الوظيفي أو البدلات...")

        grid.addWidget(QLabel("الراتب الأساسي:"), 0, 0)
        grid.addWidget(self.basic_salary_input, 0, 1)

        grid.addWidget(QLabel("إجمالي البدلات:"), 1, 0)
        grid.addWidget(self.allowances_input, 1, 1)

        grid.addWidget(QLabel("تفصيل نوع البدلات:"), 2, 0)
        grid.addWidget(self.allowance_type_edit, 2, 1)

        grid.addWidget(QLabel("إجمالي الراتب والبدلات:"), 3, 0)
        grid.addWidget(self.total_package_lbl, 3, 1)

        grid.addWidget(QLabel("تاريخ سريان الراتب:"), 4, 0)
        grid.addWidget(self.comp_effective_date, 4, 1)

        grid.addWidget(QLabel("ملاحظات مالية:"), 5, 0)
        grid.addWidget(self.comp_notes_edit, 5, 1)

        layout.addLayout(grid)
        layout.addStretch()

        self.tabs.addTab(tab, "البيانات المالية والرواتب")

    def _recalc_total_comp(self):
        if hasattr(self, "basic_salary_input"):
            tot = self.basic_salary_input.value() + self.allowances_input.value()
            self.total_package_lbl.setText(f"{tot:,.2f} ر.س")

    def _load_tech_data(self):
        with get_db() as db:
            tech = technician_service.get_technician_by_id(db, self.tech_id)
            self.emp_id_edit.setText(tech.employee_id)
            self.name_edit.setText(tech.full_name)
            self.job_title_edit.setText(tech.job_title or "")
            self.nationality_edit.setText(tech.nationality or "")
            self.id_num_edit.setText(tech.id_number or "")
            self.work_entity_edit.setText(tech.work_entity or "")
            self.phone_edit.setText(tech.phone or "")
            self.email_edit.setText(tech.email or "")

            idx = self.spec_combo.findText(tech.specialization)
            if idx >= 0:
                self.spec_combo.setCurrentIndex(idx)
            else:
                self.spec_combo.setCurrentText(tech.specialization)

            d_idx = self.dept_combo.findData(tech.department_id)
            if d_idx >= 0:
                self.dept_combo.setCurrentIndex(d_idx)

            id_t_idx = self.id_type_combo.findData(tech.id_document_type)
            if id_t_idx >= 0:
                self.id_type_combo.setCurrentIndex(id_t_idx)

            st_idx = self.status_combo.findData(tech.status)
            if st_idx >= 0:
                self.status_combo.setCurrentIndex(st_idx)

            if tech.hire_date:
                h = tech.hire_date
                self.hire_date_edit.setDate(QDate(h.year, h.month, h.day))

            user = auth_service.current_user
            if can_user(user, PERM_TECHNICIANS_SALARY_VIEW) and hasattr(self, "basic_salary_input"):
                comp = technician_service.get_compensation(db, user, self.tech_id)
                if comp:
                    self.basic_salary_input.setValue(float(comp.basic_salary or 0.0))
                    self.allowances_input.setValue(float(comp.allowances or 0.0))
                    self.allowance_type_edit.setText(comp.allowance_type or "")
                    self.comp_notes_edit.setPlainText(comp.notes or "")
                    if comp.effective_date:
                        e_d = comp.effective_date
                        self.comp_effective_date.setDate(QDate(e_d.year, e_d.month, e_d.day))
                    self._recalc_total_comp()

        self._refresh_qualifications()
        self._refresh_experiences()

    def _on_save_all(self):
        emp_id = self.emp_id_edit.text().strip()
        name = self.name_edit.text().strip()
        spec = self.spec_combo.currentText().strip()

        if not emp_id or not name:
            QMessageBox.warning(self, "خطأ في البيانات", "يرجى تعبئة الرقم الوظيفي والاسم الكامل.")
            return

        user = auth_service.current_user
        h_date = self.hire_date_edit.date().toPython()

        try:
            with get_db() as db:
                if self.tech_id:
                    tech = technician_service.update_technician(
                        db,
                        self.tech_id,
                        operator_user_id=user.id if user else None,
                        employee_id=emp_id,
                        full_name=name,
                        specialization=spec,
                        nationality=self.nationality_edit.text().strip() or None,
                        id_document_type=self.id_type_combo.currentData(),
                        id_number=self.id_num_edit.text().strip() or None,
                        job_title=self.job_title_edit.text().strip() or None,
                        department_id=self.dept_combo.currentData(),
                        work_entity=self.work_entity_edit.text().strip() or None,
                        hire_date=h_date,
                        phone=self.phone_edit.text().strip() or None,
                        email=self.email_edit.text().strip() or None,
                        status=self.status_combo.currentData()
                    )
                else:
                    tech = technician_service.create_technician(
                        db,
                        employee_id=emp_id,
                        full_name=name,
                        specialization=spec,
                        operator_user_id=user.id if user else None,
                        nationality=self.nationality_edit.text().strip() or None,
                        id_document_type=self.id_type_combo.currentData(),
                        id_number=self.id_num_edit.text().strip() or None,
                        job_title=self.job_title_edit.text().strip() or None,
                        department_id=self.dept_combo.currentData(),
                        work_entity=self.work_entity_edit.text().strip() or None,
                        hire_date=h_date,
                        phone=self.phone_edit.text().strip() or None,
                        email=self.email_edit.text().strip() or None,
                        status=self.status_combo.currentData()
                    )
                    self.tech_id = tech.id

                # Save compensation if user is authorized and form exists
                if can_user(user, PERM_TECHNICIANS_SALARY_MANAGE) and hasattr(self, "basic_salary_input"):
                    c_data = {
                        "basic_salary": self.basic_salary_input.value(),
                        "allowances": self.allowances_input.value(),
                        "allowance_type": self.allowance_type_edit.text().strip() or None,
                        "effective_date": self.comp_effective_date.date().toPython(),
                        "notes": self.comp_notes_edit.toPlainText().strip() or None
                    }
                    technician_service.set_compensation(db, user, self.tech_id, c_data)

            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))
