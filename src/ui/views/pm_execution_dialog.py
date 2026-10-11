"""
PM Execution and Inspection Recording Dialog.
Enables biomedical engineers to check off protocol tasks, input calibration readings,
and certify equipment safety compliance. Pure Arabic, RTL, zero emojis.
"""
from typing import List
from datetime import datetime
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QComboBox, QTextEdit, QPushButton, QFrame,
    QMessageBox, QWidget, QScrollArea, QCheckBox, QRadioButton,
    QButtonGroup, QDateEdit
)
from PySide6.QtCore import Qt, QDate
from src.core.i18n import tr
from src.core.database import get_db
from src.models.preventive import PMSchedule
from src.models.technician import Technician
from src.services.pm_service import pm_service
from src.ui.theme.icons import icon


class PMExecutionDialog(QDialog):
    def __init__(self, schedule_id: int, parent=None):
        super().__init__(parent)
        self.schedule_id = schedule_id
        self.setWindowTitle("تنفيذ وتوثيق الصيانة الوقائية")
        self.resize(720, 680)
        self.setMinimumSize(600, 540)

        self.checkboxes: List[QCheckBox] = []

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(14)

        # Header banner
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 8)
        header_layout.setSpacing(12)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(icon("check_double", color="#0F766E", size=26).pixmap(26, 26))

        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        dlg_title = QLabel("توثيق تنفيذ فحص ومعايرة الصيانة الوقائية")
        dlg_title.setStyleSheet("font-size: 17px; font-weight: 700; color: #0F172A;")
        dlg_sub = QLabel("تسجيل نتائج الفحص والمعايرة الفنية وشهادة السلامة الطبية للجهاز")
        dlg_sub.setStyleSheet("font-size: 12px; color: #64748B;")
        title_layout.addWidget(dlg_title)
        title_layout.addWidget(dlg_sub)

        header_layout.addWidget(icon_lbl)
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        main_layout.addWidget(header_frame)

        # Scrollable Body
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll_content = QWidget()
        body_layout = QVBoxLayout(scroll_content)
        body_layout.setSpacing(14)

        # 1. Target Equipment & Plan Details Card
        self.info_card = QFrame()
        self.info_card.setStyleSheet("background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 12px;")
        info_layout = QGridLayout(self.info_card)
        info_layout.setSpacing(8)

        self.asset_lbl = QLabel()
        self.asset_lbl.setStyleSheet("font-weight: 600; color: #0F172A;")
        self.plan_lbl = QLabel()
        self.plan_lbl.setStyleSheet("font-weight: 600; color: #0F766E;")
        self.due_lbl = QLabel()
        self.loc_lbl = QLabel()

        info_layout.addWidget(QLabel("الجهاز الطبي:"), 0, 0)
        info_layout.addWidget(self.asset_lbl, 0, 1)
        info_layout.addWidget(QLabel("خطة / بروتوكول الفحص:"), 0, 2)
        info_layout.addWidget(self.plan_lbl, 0, 3)

        info_layout.addWidget(QLabel("الموقع / القسم:"), 1, 0)
        info_layout.addWidget(self.loc_lbl, 1, 1)
        info_layout.addWidget(QLabel("تاريخ الاستحقاق:"), 1, 2)
        info_layout.addWidget(self.due_lbl, 1, 3)

        body_layout.addWidget(self.info_card)

        # 2. Execution Metadata: Technician, Date, Compliance Result
        meta_grid = QGridLayout()
        meta_grid.setSpacing(10)

        meta_grid.addWidget(QLabel("مهندس / فني الصيانة *"), 0, 0)
        self.tech_combo = QComboBox()
        meta_grid.addWidget(self.tech_combo, 0, 1)

        meta_grid.addWidget(QLabel("تاريخ التنفيذ الفعلي *"), 0, 2)
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        meta_grid.addWidget(self.date_edit, 0, 3)

        # Compliance Status (Pass / Fail)
        meta_grid.addWidget(QLabel("نتيجة الفحص والمعايرة *"), 1, 0)
        status_box = QHBoxLayout()
        self.pass_radio = QRadioButton("ناجح ومطابق للمواصفات")
        self.pass_radio.setChecked(True)
        self.pass_radio.setStyleSheet("color: #10B981; font-weight: 600;")
        
        self.fail_radio = QRadioButton("غير مطابق / يحتاج إصلاح")
        self.fail_radio.setStyleSheet("color: #EF4444; font-weight: 600;")
        
        self.status_group = QButtonGroup(self)
        self.status_group.addButton(self.pass_radio)
        self.status_group.addButton(self.fail_radio)

        status_box.addWidget(self.pass_radio)
        status_box.addWidget(self.fail_radio)
        status_box.addStretch()
        meta_grid.addLayout(status_box, 1, 1, 1, 3)

        body_layout.addLayout(meta_grid)

        # 3. Protocol Checklist Check-off Box
        checklist_box = QFrame()
        checklist_box.setStyleSheet("background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 10px;")
        self.checklist_layout = QVBoxLayout(checklist_box)
        self.checklist_layout.setSpacing(8)

        check_header = QLabel("قائمة التحقق وخطوات الفحص المعتمدة")
        check_header.setStyleSheet("font-weight: 700; color: #334155; font-size: 13px;")
        self.checklist_layout.addWidget(check_header)

        body_layout.addWidget(checklist_box)

        # 4. Calibration & Measurement Readings
        body_layout.addWidget(QLabel("قراءات المعايرة والاختبارات القياسية (أرقام/قيم)"))
        self.measurements_edit = QLineEdit()
        self.measurements_edit.setPlaceholderText("مثال: الضغط = 120/80 mmHg، تيار التسريب = 45 µA، التردد = 50.1 Hz")
        body_layout.addWidget(self.measurements_edit)

        # 5. Inspection Observations & Summary
        body_layout.addWidget(QLabel("ملاحظات وتقرير المهندس / الفني"))
        self.notes_edit = QTextEdit()
        self.notes_edit.setFixedHeight(75)
        self.notes_edit.setPlaceholderText("اكتب الملاحظات الفنية، الأجزاء التي تم تنظيفها أو ضبطها، أو التوصيات...")
        body_layout.addWidget(self.notes_edit)

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll, stretch=1)

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("إلغاء")
        cancel_btn.setIcon(icon("cancel", color="#64748B", size=14))
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("حفظ واعتماد التنفيذ")
        save_btn.setObjectName("primaryBtn")
        save_btn.setIcon(icon("save", color="#FFFFFF", size=14))
        save_btn.clicked.connect(self._on_save)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        main_layout.addLayout(btn_layout)

        self._load_schedule_and_techs()

    def _load_schedule_and_techs(self):
        with get_db() as db:
            sched = db.query(PMSchedule).filter(PMSchedule.id == self.schedule_id).first()
            if not sched:
                QMessageBox.critical(self, "خطأ", "لم يتم العثور على موعد الصيانة الوقائية المحدد.")
                self.reject()
                return

            eq = sched.equipment
            plan = sched.plan

            self.asset_lbl.setText(f"{eq.asset_number} — {eq.name_ar or eq.name_en}")
            self.plan_lbl.setText(plan.title if plan else "فحص صيانة وقائية")
            self.due_lbl.setText(str(sched.due_date))
            
            dept_name = eq.department.name_ar if eq.department else "غير محدد"
            loc_name = eq.location.room_name if eq.location else ""
            self.loc_lbl.setText(f"{dept_name} {loc_name}".strip())

            # Load technicians
            techs = db.query(Technician).filter(Technician.status == "active").all()
            for t in techs:
                self.tech_combo.addItem(f"{t.full_name} ({t.specialization or 'فني صيانة'})", t.id)

            # Build checklist items from plan
            checklist_items = plan.checklist_template if plan and plan.checklist_template else [
                "الفحص البصري والميكانيكي للجهاز",
                "التحقق من معايير السلامة الكهربائية",
                "اختبار التشغيل والأداء الوظيفي"
            ]

            for item in checklist_items:
                if isinstance(item, dict):
                    txt = item.get("task") or item.get("description") or item.get("name") or str(item)
                else:
                    txt = str(item)
                chk = QCheckBox(txt)
                chk.setChecked(True)
                chk.setStyleSheet("font-size: 13px; color: #334155; padding: 2px 0;")
                self.checklist_layout.addWidget(chk)
                self.checkboxes.append(chk)

    def _on_save(self):
        tech_id = self.tech_combo.currentData()
        if not tech_id:
            QMessageBox.warning(self, "خطأ في البيانات", "يرجى تحديد الفني / المهندس المسؤول عن التنفيذ.")
            return

        # Check if all checklist items are checked
        unchecked = [cb.text() for cb in self.checkboxes if not cb.isChecked()]
        if unchecked and self.pass_radio.isChecked():
            confirm = QMessageBox.question(
                self,
                "تأكيد الاعتماد",
                f"يوجد {len(unchecked)} بنود لم يتم التأشير عليها. هل أنت متأكد من اعتماد الفحص كناجح ومطابق؟",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if confirm != QMessageBox.StandardButton.Yes:
                return

        passed = self.pass_radio.isChecked()
        qdate = self.date_edit.date()
        exec_dt = datetime(qdate.year(), qdate.month(), qdate.day())

        measurements = {}
        meas_txt = self.measurements_edit.text().strip()
        if meas_txt:
            measurements["raw_readings"] = meas_txt

        notes = self.notes_edit.toPlainText().strip()

        try:
            with get_db() as db:
                pm_service.record_pm_execution(
                    db,
                    schedule_id=self.schedule_id,
                    technician_id=tech_id,
                    passed=passed,
                    results_summary=f"النتيجة: {'ناجح ومطابق' if passed else 'راسب / غير مطابق'}. " + notes,
                    measurements=measurements,
                    notes=notes,
                    execution_date=exec_dt
                )

            QMessageBox.information(self, "تم بنجاح", "تم تسجيل واعتماد تنفيذ الصيانة الوقائية بنجاح وتحديث تاريخ الصيانة القادم.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))
