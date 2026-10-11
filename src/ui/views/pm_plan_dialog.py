"""
PM Plan / Protocol Creation and Edit Dialog.
Enterprise 2-column form with checklist builder, pure Arabic, zero emojis.
"""
from typing import Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QComboBox, QSpinBox, QPushButton,
    QFrame, QMessageBox, QWidget, QScrollArea, QListWidget
)
from src.core.i18n import tr
from src.core.database import get_db
from src.models.equipment import Equipment
from src.services.pm_service import pm_service
from src.ui.theme.icons import icon


class PMPlanDialog(QDialog):
    def __init__(self, plan_id: Optional[int] = None, parent=None):
        super().__init__(parent)
        self.plan_id = plan_id
        self.setWindowTitle("خطة صيانة وقائية جديدة" if not plan_id else "تعديل خطة الصيانة الوقائية")
        self.resize(700, 620)
        self.setMinimumSize(580, 520)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(16)

        # Header banner
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 8)
        header_layout.setSpacing(12)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(icon("preventive", color="#0F766E", size=24).pixmap(24, 24))

        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        dlg_title = QLabel("خطة صيانة وقائية جديدة" if not plan_id else "تعديل خطة الصيانة الوقائية")
        dlg_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #0F172A;")
        dlg_sub = QLabel("تحديد بروتوكول وفترات الفحص والمعايرة الدورية للأجهزة الطبية")
        dlg_sub.setStyleSheet("font-size: 12px; color: #64748B;")
        title_layout.addWidget(dlg_title)
        title_layout.addWidget(dlg_sub)

        header_layout.addWidget(icon_lbl)
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        main_layout.addWidget(header_frame)

        # Scrollable form body
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll_content = QWidget()
        form_layout = QVBoxLayout(scroll_content)
        form_layout.setSpacing(12)

        grid = QGridLayout()
        grid.setSpacing(10)

        # 1. Plan Title
        grid.addWidget(QLabel("عنوان الخطة / البروتوكول *"), 0, 0)
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("مثال: الفحص الدوري والمعايرة الربع سنوية لأجهزة التنفس الصناعي")
        grid.addWidget(self.title_edit, 0, 1, 1, 3)

        # 2. Frequency & Duration
        grid.addWidget(QLabel("دورية الصيانة (بالأيام) *"), 1, 0)
        self.freq_spin = QSpinBox()
        self.freq_spin.setRange(1, 3650)
        self.freq_spin.setValue(90)
        grid.addWidget(self.freq_spin, 1, 1)

        # Frequency Quick Presets
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(["مخصص", "30 يوم (شهري)", "90 يوم (ربع سنوي)", "180 يوم (نصف سنوي)", "365 يوم (سنوي)"])
        self.preset_combo.setCurrentIndex(2)
        self.preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        grid.addWidget(self.preset_combo, 1, 2)

        grid.addWidget(QLabel("المدة المتوقعة"), 1, 3)
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(10, 1440)
        self.duration_spin.setValue(60)
        self.duration_spin.setSuffix(" دقيقة")
        grid.addWidget(self.duration_spin, 1, 4)

        # 3. Target Scope: Category or Specific Equipment
        grid.addWidget(QLabel("التطبيق على تصنيف كامل"), 2, 0)
        self.category_combo = QComboBox()
        self.category_combo.addItem("-- اختر التصنيف الطبي --", "")
        grid.addWidget(self.category_combo, 2, 1, 1, 2)

        grid.addWidget(QLabel("أو تطبيق على جهاز محدد"), 2, 3)
        self.equipment_combo = QComboBox()
        self.equipment_combo.addItem("-- اختياري: جهاز محدد --", None)
        grid.addWidget(self.equipment_combo, 2, 4)

        form_layout.addLayout(grid)

        # 4. Checklist Builder Section
        form_layout.addWidget(QLabel("قائمة بنود الفحص والمعايرة (Checklist)"))
        
        check_input_layout = QHBoxLayout()
        self.checklist_item_edit = QLineEdit()
        self.checklist_item_edit.setPlaceholderText("اكتب خطوة الفحص أو الاختبار هنا...")
        self.checklist_item_edit.returnPressed.connect(self._add_checklist_item)
        
        add_item_btn = QPushButton("إضافة بند")
        add_item_btn.setIcon(icon("add", color="#0F766E", size=14))
        add_item_btn.clicked.connect(self._add_checklist_item)
        
        del_item_btn = QPushButton("حذف المحدد")
        del_item_btn.setIcon(icon("delete", color="#EF4444", size=14))
        del_item_btn.clicked.connect(self._remove_checklist_item)

        check_input_layout.addWidget(self.checklist_item_edit, stretch=1)
        check_input_layout.addWidget(add_item_btn)
        check_input_layout.addWidget(del_item_btn)
        form_layout.addLayout(check_input_layout)

        self.checklist_list = QListWidget()
        self.checklist_list.setFixedHeight(160)
        self.checklist_list.setStyleSheet("background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px;")
        form_layout.addWidget(self.checklist_list)

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll, stretch=1)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("إلغاء")
        cancel_btn.setIcon(icon("cancel", color="#64748B", size=14))
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("حفظ الخطة")
        save_btn.setObjectName("primaryBtn")
        save_btn.setIcon(icon("save", color="#FFFFFF", size=14))
        save_btn.clicked.connect(self._on_save)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        main_layout.addLayout(btn_layout)

        self._populate_options()
        if self.plan_id:
            self._load_plan_data()
        else:
            self._add_default_checklist()

    def _on_preset_changed(self, index: int):
        mapping = {1: 30, 2: 90, 3: 180, 4: 365}
        if index in mapping:
            self.freq_spin.setValue(mapping[index])

    def _populate_options(self):
        with get_db() as db:
            categories = [c[0] for c in db.query(Equipment.category).distinct().filter(Equipment.category.isnot(None)).all()]
            for cat in sorted(categories):
                self.category_combo.addItem(cat, cat)

            eqs = db.query(Equipment).filter(Equipment.status.in_(["operational", "standby", "under_maintenance"])).all()
            for eq in eqs:
                self.equipment_combo.addItem(f"{eq.asset_number} — {eq.name_ar or eq.name_en}", eq.id)

    def _add_default_checklist(self):
        default_items = [
            "الفحص البصري للهيكل والكابلات ومنافذ التوصيل للتأكد من السلامة الفيزيائية",
            "اختبار السلامة الكهربائية (مقاومة التأريض وتيار التسريب)",
            "فحص واختبار أداء البطارية الاحتياطية وزمن التشغيل عند انقطاع التيار",
            "المعايرة والتحقق من دقة القراءات والمعايير التشغيلية بالمحاكي القياسي",
            "تنظيف واستبدال فلاتر الهواء وفحص الحساسات الداخلية"
        ]
        for item in default_items:
            self.checklist_list.addItem(item)

    def _add_checklist_item(self):
        text = self.checklist_item_edit.text().strip()
        if text:
            self.checklist_list.addItem(text)
            self.checklist_item_edit.clear()

    def _remove_checklist_item(self):
        row = self.checklist_list.currentRow()
        if row >= 0:
            self.checklist_list.takeItem(row)

    def _load_plan_data(self):
        with get_db() as db:
            plan = pm_service.get_pm_plan(db, self.plan_id)
            if not plan:
                return
            self.title_edit.setText(plan.title)
            self.freq_spin.setValue(plan.frequency_days)
            self.duration_spin.setValue(plan.estimated_duration_minutes)

            if plan.category:
                idx = self.category_combo.findData(plan.category)
                if idx >= 0:
                    self.category_combo.setCurrentIndex(idx)

            if plan.equipment_id:
                idx = self.equipment_combo.findData(plan.equipment_id)
                if idx >= 0:
                    self.equipment_combo.setCurrentIndex(idx)

            self.checklist_list.clear()
            for item in (plan.checklist_template or []):
                if isinstance(item, dict):
                    txt = item.get("task") or item.get("description") or item.get("name") or str(item)
                else:
                    txt = str(item)
                self.checklist_list.addItem(txt)

    def _on_save(self):
        title = self.title_edit.text().strip()
        if not title:
            QMessageBox.warning(self, "خطأ في البيانات", "يرجى كتابة عنوان الخطة أو البروتوكول.")
            return

        cat = self.category_combo.currentData()
        eq_id = self.equipment_combo.currentData()

        if not cat and not eq_id:
            QMessageBox.warning(self, "خطأ في البيانات", "يرجى اختيار تصنيف الأجهزة أو اختيار جهاز محدد لتطبيق الخطة عليه.")
            return

        checklist = [self.checklist_list.item(i).text() for i in range(self.checklist_list.count())]

        try:
            with get_db() as db:
                if self.plan_id:
                    pm_service.update_pm_plan(
                        db,
                        self.plan_id,
                        title=title,
                        frequency_days=self.freq_spin.value(),
                        estimated_duration_minutes=self.duration_spin.value(),
                        category=cat or None,
                        equipment_id=eq_id or None,
                        checklist_template=checklist
                    )
                else:
                    plan = pm_service.create_pm_plan(
                        db,
                        title=title,
                        frequency_days=self.freq_spin.value(),
                        checklist_template=checklist,
                        estimated_duration_minutes=self.duration_spin.value(),
                        category=cat or None,
                        equipment_id=eq_id or None
                    )
                    # Automatically generate initial schedule for target assets
                    pm_service.generate_schedules_for_plan(db, plan.id)

            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))
