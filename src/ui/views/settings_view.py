"""
System Settings View.
Hospital identity configuration, database backup/restore, system information,
and automated monthly reports management & history archive.
Pure Arabic, RTL, zero emojis.
"""
import os
import sys
from datetime import datetime, date
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QGroupBox, QFormLayout, QLineEdit, QMessageBox,
    QFileDialog, QFrame, QComboBox, QSpinBox, QCheckBox,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices

from src.core.i18n import tr
from src.core.database import get_db
from src.models.hospital import Hospital
from src.models.user import User
from src.services.backup_service import backup_service
from src.services.monthly_report_service import monthly_report_service
from src.ui.theme.icons import icon


class SettingsView(QWidget):
    ARABIC_MONTHS = [
        "يناير (01)", "فبراير (02)", "مارس (03)", "أبريل (04)",
        "مايو (05)", "يونيو (06)", "يوليو (07)", "أغسطس (08)",
        "سبتمبر (09)", "أكتوبر (10)", "نوفمبر (11)", "ديسمبر (12)"
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._load_system_info()
        self._load_hospital_identity()
        self._load_monthly_reports()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 14, 18, 14)
        main_layout.setSpacing(10)

        # Header
        header_layout = QHBoxLayout()
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)

        self.title_lbl = QLabel("إعدادات النظام والتقارير المؤتمتة")
        self.title_lbl.setStyleSheet("font-size: 18px; font-weight: 800; color: #0F172A;")
        self.sub_lbl = QLabel("تهيئة هوية المنشأة، إدارة النسخ الاحتياطية، وأرشيف التقارير الشهرية الآلية")
        self.sub_lbl.setStyleSheet("font-size: 12px; color: #64748B;")
        title_layout.addWidget(self.title_lbl)
        title_layout.addWidget(self.sub_lbl)
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                background-color: #FFFFFF;
                top: -1px;
            }
            QTabBar::tab {
                background: #F1F5F9;
                color: #64748B;
                padding: 8px 16px;
                font-weight: 600;
                font-size: 12px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-left: 4px;
            }
            QTabBar::tab:selected {
                background: #FFFFFF;
                color: #0F766E;
                border: 1px solid #E2E8F0;
                border-bottom: 2px solid #0F766E;
            }
        """)

        # --- Tab 1: Hospital Identity ---
        identity_tab = QWidget()
        identity_layout = QVBoxLayout(identity_tab)
        identity_layout.setContentsMargins(14, 14, 14, 14)
        identity_layout.setSpacing(10)

        grp = QGroupBox("هوية المنشأة والمستشفى")
        grp_layout = QFormLayout(grp)
        grp_layout.setSpacing(10)

        self.hospital_name_ar_edit = QLineEdit()
        self.hospital_name_ar_edit.setPlaceholderText("مثال: مستشفى الملك فهد التخصصي")
        self.hospital_name_en_edit = QLineEdit()
        self.hospital_name_en_edit.setPlaceholderText("e.g., King Fahd Specialist Hospital")
        self.hospital_code_edit = QLineEdit()
        self.hospital_code_edit.setPlaceholderText("مثال: KFSH-001")
        self.hospital_phone_edit = QLineEdit()
        self.hospital_phone_edit.setPlaceholderText("مثال: +966 11 000 0000")
        self.hospital_address_edit = QLineEdit()
        self.hospital_address_edit.setPlaceholderText("المدينة، الحي، الرمز البريدي")

        grp_layout.addRow("اسم المنشأة (بالعربية) *:", self.hospital_name_ar_edit)
        grp_layout.addRow("الاسم (بالإنجليزية):", self.hospital_name_en_edit)
        grp_layout.addRow("كود المنشأة *:", self.hospital_code_edit)
        grp_layout.addRow("رقم الهاتف / التواصل:", self.hospital_phone_edit)
        grp_layout.addRow("العنوان:", self.hospital_address_edit)

        save_identity_btn = QPushButton("حفظ بيانات المنشأة")
        save_identity_btn.setObjectName("primaryBtn")
        save_identity_btn.setIcon(icon("save", color="#FFFFFF", size=14))
        save_identity_btn.clicked.connect(self._save_identity)

        identity_layout.addWidget(grp)
        identity_layout.addWidget(save_identity_btn, alignment=Qt.AlignmentFlag.AlignRight)
        identity_layout.addStretch()
        self.tabs.addTab(identity_tab, "الهوية والمنشأة الطبية")

        # --- Tab 2: Database & Backup ---
        db_tab = QWidget()
        db_layout = QVBoxLayout(db_tab)
        db_layout.setContentsMargins(14, 14, 14, 14)
        db_layout.setSpacing(12)

        self.db_info_card = QFrame()
        self.db_info_card.setStyleSheet("""
            QFrame {
                background-color: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        db_info_layout = QFormLayout(self.db_info_card)
        db_info_layout.setSpacing(8)

        self.db_size_lbl = QLabel("-")
        self.db_modified_lbl = QLabel("-")
        self.db_path_lbl = QLabel("-")
        self.db_path_lbl.setWordWrap(True)
        self.db_path_lbl.setStyleSheet("color: #64748B; font-size: 11px;")

        db_info_layout.addRow("حجم قاعدة البيانات الحالية:", self.db_size_lbl)
        db_info_layout.addRow("آخر تعديل / حفظ:", self.db_modified_lbl)
        db_info_layout.addRow("مسار الملف:", self.db_path_lbl)

        db_layout.addWidget(self.db_info_card)

        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(10)

        backup_btn = QPushButton("إنشاء نسخة احتياطية فورية")
        backup_btn.setObjectName("primaryBtn")
        backup_btn.setIcon(icon("backup", color="#FFFFFF", size=14))
        backup_btn.clicked.connect(self._create_backup)
        actions_layout.addWidget(backup_btn)

        restore_btn = QPushButton("استعادة نسخة احتياطية")
        restore_btn.setIcon(icon("history", color="#475569", size=14))
        restore_btn.clicked.connect(self._restore_backup)
        actions_layout.addWidget(restore_btn)

        actions_layout.addStretch()
        db_layout.addLayout(actions_layout)
        db_layout.addStretch()
        self.tabs.addTab(db_tab, "قاعدة البيانات والنسخ الاحتياطي")

        # --- Tab 3: Automated Monthly Reports ---
        reports_tab = QWidget()
        reports_layout = QVBoxLayout(reports_tab)
        reports_layout.setContentsMargins(14, 14, 14, 14)
        reports_layout.setSpacing(10)

        # Controls & Generator Card
        gen_card = QFrame()
        gen_card.setStyleSheet("""
            QFrame {
                background-color: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        gen_layout = QHBoxLayout(gen_card)
        gen_layout.setContentsMargins(10, 8, 10, 8)
        gen_layout.setSpacing(12)

        # Month Selector
        m_layout = QVBoxLayout()
        m_layout.setSpacing(2)
        m_lbl = QLabel("الشهر:")
        m_lbl.setStyleSheet("font-size: 11px; font-weight: bold; color: #475569;")
        self.month_combo = QComboBox()
        for idx, m_name in enumerate(self.ARABIC_MONTHS, start=1):
            self.month_combo.addItem(m_name, idx)
        today = date.today()
        # Default to previous month
        prev_m = 12 if today.month == 1 else today.month - 1
        self.month_combo.setCurrentIndex(prev_m - 1)
        m_layout.addWidget(m_lbl)
        m_layout.addWidget(self.month_combo)
        gen_layout.addLayout(m_layout)

        # Year Selector
        y_layout = QVBoxLayout()
        y_layout.setSpacing(2)
        y_lbl = QLabel("السنة:")
        y_lbl.setStyleSheet("font-size: 11px; font-weight: bold; color: #475569;")
        self.year_spin = QSpinBox()
        self.year_spin.setRange(2020, 2040)
        prev_y = today.year - 1 if today.month == 1 else today.year
        self.year_spin.setValue(prev_y)
        y_layout.addWidget(y_lbl)
        y_layout.addWidget(self.year_spin)
        gen_layout.addLayout(y_layout)

        # Force regenerate checkbox
        f_layout = QVBoxLayout()
        f_layout.setSpacing(2)
        f_layout.addSpacing(16)
        self.force_check = QCheckBox("إعادة توليد وتجاوز الموجود")
        self.force_check.setStyleSheet("font-size: 11px; color: #475569;")
        f_layout.addWidget(self.force_check)
        gen_layout.addLayout(f_layout)

        # Generate Button
        btn_gen_layout = QVBoxLayout()
        btn_gen_layout.setSpacing(2)
        btn_gen_layout.addSpacing(16)
        self.generate_btn = QPushButton("توليد تقارير الشهر")
        self.generate_btn.setIcon(icon("reports", color="#FFFFFF", size=14))
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #0F766E;
                color: #FFFFFF;
                font-weight: 700;
                font-size: 12px;
                padding: 6px 14px;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #0D9488; }
        """)
        self.generate_btn.clicked.connect(self._generate_selected_monthly_reports)
        btn_gen_layout.addWidget(self.generate_btn)
        gen_layout.addLayout(btn_gen_layout)

        # Open Reports Directory
        btn_open_layout = QVBoxLayout()
        btn_open_layout.setSpacing(2)
        btn_open_layout.addSpacing(16)
        self.open_dir_btn = QPushButton("فتح مجلد التقارير")
        self.open_dir_btn.setIcon(icon("folder", color="#334155", size=14))
        self.open_dir_btn.setStyleSheet("""
            QPushButton {
                background-color: #E2E8F0;
                color: #334155;
                font-weight: 600;
                font-size: 12px;
                padding: 6px 12px;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #CBD5E1; }
        """)
        self.open_dir_btn.clicked.connect(self._open_reports_directory)
        btn_open_layout.addWidget(self.open_dir_btn)
        gen_layout.addLayout(btn_open_layout)

        # Refresh List
        btn_ref_layout = QVBoxLayout()
        btn_ref_layout.setSpacing(2)
        btn_ref_layout.addSpacing(16)
        self.refresh_reports_btn = QPushButton("تحديث الأرشيف")
        self.refresh_reports_btn.setIcon(icon("refresh", color="#475569", size=14))
        self.refresh_reports_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                border: 1px solid #CBD5E1;
                color: #475569;
                font-size: 12px;
                padding: 6px 12px;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #F1F5F9; }
        """)
        self.refresh_reports_btn.clicked.connect(self._load_monthly_reports)
        btn_ref_layout.addWidget(self.refresh_reports_btn)
        gen_layout.addLayout(btn_ref_layout)

        gen_layout.addStretch()
        reports_layout.addWidget(gen_card)

        # Reports Archive Table
        self.reports_table = QTableWidget()
        self.reports_table.setColumnCount(7)
        self.reports_table.setHorizontalHeaderLabels([
            "المعرف", "عنوان التقرير", "الفترة", "تاريخ التوليد", "الحالة", "عدد السجلات", "الإجراءات والتحميل"
        ])
        self.reports_table.setColumnWidth(0, 60)
        self.reports_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.reports_table.setColumnWidth(2, 90)
        self.reports_table.setColumnWidth(3, 160)
        self.reports_table.setColumnWidth(4, 85)
        self.reports_table.setColumnWidth(5, 95)
        self.reports_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.reports_table.setColumnWidth(6, 180)
        self.reports_table.setAlternatingRowColors(True)
        self.reports_table.verticalHeader().setDefaultSectionSize(40)
        self.reports_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #E2E8F0;
                border-radius: 6px;
                background-color: #FFFFFF;
            }
        """)
        reports_layout.addWidget(self.reports_table, stretch=1)
        self.tabs.addTab(reports_tab, "التقارير الشهرية المؤتمتة")

        # --- Tab 4: System Info ---
        sys_tab = QWidget()
        sys_layout = QVBoxLayout(sys_tab)
        sys_layout.setContentsMargins(14, 14, 14, 14)
        sys_layout.setSpacing(10)

        sys_grp = QGroupBox("معلومات النظام والبيئة التشغيلية")
        sys_grp_layout = QFormLayout(sys_grp)
        sys_grp_layout.setSpacing(8)

        self.version_lbl = QLabel("MEMMS Enterprise 2.0 (Medical Equipment Maintenance Management System)")
        self.version_lbl.setStyleSheet("font-weight: 700; color: #0F766E;")
        self.users_lbl = QLabel("-")
        self.py_lbl = QLabel("-")
        self.os_lbl = QLabel(f"{sys.platform} (Windows)")

        sys_grp_layout.addRow("إصدار النظام:", self.version_lbl)
        sys_grp_layout.addRow("عدد المستخدمين النشطين:", self.users_lbl)
        sys_grp_layout.addRow("بيئة تشغيل Python:", self.py_lbl)
        sys_grp_layout.addRow("نظام التشغيل:", self.os_lbl)

        sys_layout.addWidget(sys_grp)
        sys_layout.addStretch()
        self.tabs.addTab(sys_tab, "معلومات النظام")

        main_layout.addWidget(self.tabs, stretch=1)

    def _load_hospital_identity(self):
        with get_db() as db:
            hosp = db.query(Hospital).first()
            if hosp:
                self.hospital_name_ar_edit.setText(hosp.name_ar or "")
                self.hospital_name_en_edit.setText(hosp.name_en or "")
                self.hospital_code_edit.setText(hosp.code or "")
                self.hospital_phone_edit.setText(hosp.phone or "")
                self.hospital_address_edit.setText(hosp.address or "")

    def _load_system_info(self):
        self.py_lbl.setText(f"Python {sys.version.split()[0]}")

        db_info = backup_service.get_database_info()
        if db_info["exists"]:
            self.db_size_lbl.setText(f"{db_info['size_mb']} ميجابايت ({db_info['size_bytes']:,} بايت)")
            self.db_modified_lbl.setText(str(db_info["last_modified"]))
            from config import DEFAULT_SQLITE_PATH
            self.db_path_lbl.setText(str(DEFAULT_SQLITE_PATH))

        with get_db() as db:
            user_count = db.query(User).filter(User.is_active.is_(True)).count()
            self.users_lbl.setText(f"{user_count} مستخدم")

    def _save_identity(self):
        name_ar = self.hospital_name_ar_edit.text().strip()
        code = self.hospital_code_edit.text().strip()
        if not name_ar or not code:
            QMessageBox.warning(self, "خطأ في البيانات", "يرجى تعبئة اسم المنشأة وكود المنشأة.")
            return

        with get_db() as db:
            hosp = db.query(Hospital).first()
            if not hosp:
                hosp = Hospital(
                    name_ar=name_ar,
                    name_en=self.hospital_name_en_edit.text().strip() or name_ar,
                    code=code,
                    phone=self.hospital_phone_edit.text().strip() or None,
                    address=self.hospital_address_edit.text().strip() or None
                )
                db.add(hosp)
            else:
                hosp.name_ar = name_ar
                hosp.name_en = self.hospital_name_en_edit.text().strip() or name_ar
                hosp.code = code
                hosp.phone = self.hospital_phone_edit.text().strip() or None
                hosp.address = self.hospital_address_edit.text().strip() or None
            db.commit()

        QMessageBox.information(self, "تم بنجاح", "تم حفظ وتحديث بيانات هوية المنشأة الطبية بنجاح.")

    def _create_backup(self):
        try:
            path = backup_service.create_backup()
            QMessageBox.information(
                self, "تم إنشاء النسخة الاحتياطية",
                f"تم حفظ النسخة الاحتياطية لقاعدة البيانات بنجاح في:\n\n{path}"
            )
            self._load_system_info()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل إنشاء النسخة الاحتياطية: {str(e)}")

    def _restore_backup(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "اختر ملف النسخة الاحتياطية للاستعادة",
            backup_service.get_backups_dir(),
            "قاعدة بيانات MEMMS (*.db)"
        )
        if not path:
            return
        try:
            backup_service.restore_backup(path)
            QMessageBox.information(self, "تمت الاستعادة", "تم استعادة قاعدة البيانات بنجاح من النسخة المحددة.")
            self._load_system_info()
            self._load_hospital_identity()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل استعادة النسخة الاحتياطية: {str(e)}")

    # ── Monthly Reports Handlers ─────────────────────────────────────────────
    def _load_monthly_reports(self):
        try:
            with get_db() as db:
                reports = monthly_report_service.get_generated_reports_history(db)
                self.reports_table.setRowCount(len(reports))

                for r_idx, rep in enumerate(reports):
                    self.reports_table.setItem(r_idx, 0, QTableWidgetItem(str(rep.id)))
                    title_text = rep.title if getattr(rep, "title", None) else rep.report_type
                    self.reports_table.setItem(r_idx, 1, QTableWidgetItem(title_text))
                    self.reports_table.setItem(r_idx, 2, QTableWidgetItem(f"{rep.period_year}/{rep.period_month:02d}"))
                    
                    gen_at_str = rep.generated_at.strftime("%Y-%m-%d %H:%M") if getattr(rep, "generated_at", None) else "-"
                    self.reports_table.setItem(r_idx, 3, QTableWidgetItem(gen_at_str))

                    status_str = "ناجح" if rep.status == "success" else rep.status
                    status_item = QTableWidgetItem(status_str)
                    if rep.status == "success":
                        status_item.setForeground(Qt.GlobalColor.darkGreen)
                    self.reports_table.setItem(r_idx, 4, status_item)

                    self.reports_table.setItem(r_idx, 5, QTableWidgetItem("—"))

                    # Action buttons (Open PDF, Open Excel)
                    act_widget = QWidget()
                    act_layout = QHBoxLayout(act_widget)
                    act_layout.setContentsMargins(4, 2, 4, 2)
                    act_layout.setSpacing(6)

                    pdf_file = rep.file_path_pdf or getattr(rep, "pdf_path", "")
                    pdf_btn = QPushButton("PDF")
                    pdf_btn.setIcon(icon("export_pdf", color="#DC2626", size=13))
                    pdf_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #FEE2E2;
                            color: #991B1B;
                            font-weight: 700;
                            font-size: 11px;
                            padding: 3px 8px;
                            border-radius: 4px;
                        }
                        QPushButton:hover { background-color: #FECACA; }
                    """)
                    pdf_btn.setEnabled(bool(pdf_file and os.path.exists(pdf_file)))
                    pdf_btn.clicked.connect(lambda _, p=pdf_file: self._open_file(p))
                    act_layout.addWidget(pdf_btn)

                    excel_file = rep.file_path_excel or getattr(rep, "excel_path", "")
                    excel_btn = QPushButton("Excel")
                    excel_btn.setIcon(icon("export_excel", color="#059669", size=13))
                    excel_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #D1FAE5;
                            color: #065F46;
                            font-weight: 700;
                            font-size: 11px;
                            padding: 3px 8px;
                            border-radius: 4px;
                        }
                        QPushButton:hover { background-color: #A7F3D0; }
                    """)
                    excel_btn.setEnabled(bool(excel_file and os.path.exists(excel_file)))
                    excel_btn.clicked.connect(lambda _, p=excel_file: self._open_file(p))
                    act_layout.addWidget(excel_btn)

                    self.reports_table.setCellWidget(r_idx, 6, act_widget)

                for r in range(len(reports)):
                    for c in [0, 2, 3, 4, 5]:
                        it = self.reports_table.item(r, c)
                        if it:
                            it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        except Exception as e:
            print(f"Error loading monthly reports archive: {e}")

    def _generate_selected_monthly_reports(self):
        month = self.month_combo.currentData()
        year = self.year_spin.value()
        force = self.force_check.isChecked()

        try:
            with get_db() as db:
                reports = monthly_report_service.generate_all_monthly_reports(
                    db, year=year, month=month, force=force
                )
            self._load_monthly_reports()
            QMessageBox.information(
                self, "تم التوليد بنجاح",
                f"تم توليد وأرشفة {len(reports)} تقارير شهرية لشهر {year}/{month:02d} بنجاح كملفات PDF و Excel."
            )
        except Exception as e:
            QMessageBox.critical(self, "خطأ في التوليد", f"فشل توليد التقارير الشهرية: {str(e)}")

    def _open_file(self, filepath: str):
        if not filepath or not os.path.exists(filepath):
            QMessageBox.warning(self, "تنبيه", "الملف المطلوب غير موجود على القرص.")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(filepath))

    def _open_reports_directory(self):
        rdir = str(monthly_report_service.reports_dir)
        if os.path.exists(rdir):
            QDesktopServices.openUrl(QUrl.fromLocalFile(rdir))
        else:
            QMessageBox.warning(self, "تنبيه", "مجلد التقارير لم يتم إنشاؤه بعد.")

    def retranslate_ui(self):
        self._load_system_info()
        self._load_hospital_identity()
        self._load_monthly_reports()
