"""
Work Order Dialog for creating and modifying corrective maintenance tasks.
Pure Arabic, RTL, zero emojis, technician assignment, costs and diagnosis support.
"""
from typing import Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QComboBox, QTextEdit, QPushButton, QMessageBox,
    QDoubleSpinBox, QFrame, QScrollArea, QWidget
)
from src.core.i18n import tr
from src.core.database import get_db
from src.services.work_order_service import work_order_service
from src.services.equipment_service import equipment_service
from src.services.auth_service import auth_service
from src.models.work_order import WorkOrder
from src.models.technician import Technician
from src.models.equipment import Equipment
from src.ui.theme.icons import icon


class WorkOrderDialog(QDialog):
    def __init__(self, work_order: Optional[WorkOrder] = None, parent=None):
        super().__init__(parent)
        self.work_order = work_order
        action_title = "تعديل أمر صيانة" if work_order else "فتح أمر صيانة جديد"
        self.setWindowTitle(f"{action_title} — نظام إدارة الصيانة الطبية")
        self.resize(720, 640)
        self.setMinimumSize(600, 520)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Header
        header_frame = QFrame()
        h_layout = QHBoxLayout(header_frame)
        h_layout.setContentsMargins(0, 0, 0, 4)
        h_layout.setSpacing(12)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(icon("work_orders", color="#0F766E", size=26).pixmap(26, 26))

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title_lbl = QLabel(action_title)
        title_lbl.setStyleSheet("font-size: 18px; font-weight: 800; color: #0F172A;")
        sub_lbl = QLabel("تسجيل بلاغ عطل طارئ، تكليف الفني، وتوثيق خطوات الإصلاح والتكاليف")
        sub_lbl.setStyleSheet("font-size: 12px; color: #64748B;")
        title_box.addWidget(title_lbl)
        title_box.addWidget(sub_lbl)

        h_layout.addWidget(icon_lbl)
        h_layout.addLayout(title_box)
        h_layout.addStretch()
        layout.addWidget(header_frame)

        # Scroll area for form
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll_content = QWidget()
        form_layout = QVBoxLayout(scroll_content)
        form_layout.setSpacing(12)

        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(12)

        self.eq_combo = QComboBox()
        self.reported_by_input = QLineEdit()
        self.contact_input = QLineEdit()

        self.priority_combo = QComboBox()
        for p in ["critical", "high", "medium", "low"]:
            self.priority_combo.addItem(tr(f"priority.{p}"), p)
        self.priority_combo.setCurrentIndex(2)  # Medium default

        self.status_combo = QComboBox()
        for s in ["pending", "assigned", "in_progress", "waiting_parts", "completed", "closed", "cancelled"]:
            self.status_combo.addItem(tr(f"status.{s}"), s)

        self.tech_combo = QComboBox()
        self.tech_combo.addItem("-- غير مخصص بعد --", None)

        self.labor_cost_spin = QDoubleSpinBox()
        self.labor_cost_spin.setRange(0.0, 999999.0)
        self.labor_cost_spin.setDecimals(2)
        self.labor_cost_spin.setSuffix(" ر.س")

        self.parts_cost_spin = QDoubleSpinBox()
        self.parts_cost_spin.setRange(0.0, 999999.0)
        self.parts_cost_spin.setDecimals(2)
        self.parts_cost_spin.setSuffix(" ر.س")

        self.desc_input = QTextEdit()
        self.desc_input.setMaximumHeight(70)
        self.desc_input.setPlaceholderText("اكتب وصف العطل بالتفصيل...")

        self.symptoms_input = QLineEdit()
        self.symptoms_input.setPlaceholderText("الأعراض الظاهرة على الجهاز...")

        self.diagnosis_input = QTextEdit()
        self.diagnosis_input.setMaximumHeight(60)
        self.diagnosis_input.setPlaceholderText("التشخيص الفني للعطل...")

        self.action_input = QTextEdit()
        self.action_input.setMaximumHeight(60)
        self.action_input.setPlaceholderText("الإجراءات التصحيحية التي تم اتخاذها...")

        # Form layout
        self._add_field(grid, 0, 0, "الجهاز الطبي المتأثر *", self.eq_combo)
        self._add_field(grid, 0, 1, "الأولوية ودرجة الأهمية *", self.priority_combo)

        self._add_field(grid, 1, 0, "اسم مقدم البلاغ *", self.reported_by_input)
        self._add_field(grid, 1, 1, "وسيلة التواصل / الهاتف", self.contact_input)

        self._add_field(grid, 2, 0, "حالة أمر الصيانة", self.status_combo)
        self._add_field(grid, 2, 1, "الفني / المهندس المسؤول", self.tech_combo)

        self._add_field(grid, 3, 0, "تكلفة أجور الصيانة (عمالة)", self.labor_cost_spin)
        self._add_field(grid, 3, 1, "تكلفة قطع الغيار", self.parts_cost_spin)

        form_layout.addLayout(grid)

        # Failure description
        desc_box = QVBoxLayout()
        desc_lbl = QLabel("وصف العطل والمشكلة *")
        desc_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #475569;")
        desc_box.addWidget(desc_lbl)
        desc_box.addWidget(self.desc_input)
        form_layout.addLayout(desc_box)

        # Symptoms
        symp_box = QVBoxLayout()
        symp_lbl = QLabel("الأعراض الظاهرة")
        symp_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #475569;")
        symp_box.addWidget(symp_lbl)
        symp_box.addWidget(self.symptoms_input)
        form_layout.addLayout(symp_box)

        # Diagnosis
        diag_box = QVBoxLayout()
        diag_lbl = QLabel("التشخيص الفني وسبب العطل")
        diag_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #475569;")
        diag_box.addWidget(diag_lbl)
        diag_box.addWidget(self.diagnosis_input)
        form_layout.addLayout(diag_box)

        # Corrective Action
        action_box = QVBoxLayout()
        action_lbl = QLabel("الإجراء التصحيحي المتخذ")
        action_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #475569;")
        action_box.addWidget(action_lbl)
        action_box.addWidget(self.action_input)
        form_layout.addLayout(action_box)

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, stretch=1)

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.addStretch()

        cancel_btn = QPushButton("إلغاء")
        cancel_btn.setIcon(icon("cancel", color="#64748B", size=14))
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("حفظ أمر الصيانة")
        save_btn.setObjectName("primaryBtn")
        save_btn.setIcon(icon("save", color="#FFFFFF", size=14))
        save_btn.clicked.connect(self._save)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

        self._load_options()
        if self.work_order:
            self._load_data()

    def _add_field(self, grid: QGridLayout, row: int, col: int, label_text: str, widget):
        box = QVBoxLayout()
        box.setSpacing(4)
        lbl = QLabel(label_text)
        lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #475569;")
        box.addWidget(lbl)
        box.addWidget(widget)
        grid.addLayout(box, row, col)

    def _load_options(self):
        with get_db() as db:
            items = equipment_service.get_equipment_list(db, limit=500)
            self.eq_combo.clear()
            for eq in items:
                name = eq.name_ar or eq.name_en or "جهاز طبي"
                self.eq_combo.addItem(f"{eq.asset_number} — {name}", eq.id)

            techs = db.query(Technician).filter(Technician.status == "active").all()
            for t in techs:
                self.tech_combo.addItem(f"{t.full_name} ({t.specialization or 'فني'})", t.id)

    def _load_data(self):
        wo = self.work_order
        idx = self.eq_combo.findData(wo.equipment_id)
        if idx >= 0:
            self.eq_combo.setCurrentIndex(idx)
            self.eq_combo.setEnabled(False)

        self.reported_by_input.setText(wo.reported_by_name or "")
        self.contact_input.setText(wo.reporter_contact or "")

        p_idx = self.priority_combo.findData(wo.priority)
        if p_idx >= 0:
            self.priority_combo.setCurrentIndex(p_idx)

        s_idx = self.status_combo.findData(wo.status)
        if s_idx >= 0:
            self.status_combo.setCurrentIndex(s_idx)

        if wo.assigned_technician_id:
            t_idx = self.tech_combo.findData(wo.assigned_technician_id)
            if t_idx >= 0:
                self.tech_combo.setCurrentIndex(t_idx)

        self.labor_cost_spin.setValue(wo.total_labor_cost or 0.0)
        self.parts_cost_spin.setValue(wo.total_parts_cost or 0.0)

        self.desc_input.setPlainText(wo.failure_description or "")
        self.symptoms_input.setText(wo.symptoms or "")
        self.diagnosis_input.setPlainText(wo.diagnosis or "")
        self.action_input.setPlainText(wo.corrective_action or "")

    def _save(self):
        eq_id = self.eq_combo.currentData()
        reported_by = self.reported_by_input.text().strip()
        desc = self.desc_input.toPlainText().strip()

        if not eq_id or not reported_by or not desc:
            QMessageBox.warning(self, "خطأ في البيانات", "يرجى تعبئة الحقول الإلزامية المطلوبة (الجهاز، مقدم البلاغ، وصف العطل).")
            return

        with get_db() as db:
            eq = db.query(Equipment).filter(Equipment.id == eq_id).first()
            dept_id = eq.department_id if eq and eq.department_id else 1

        data = {
            "equipment_id": eq_id,
            "department_id": dept_id,
            "reported_by_name": reported_by,
            "reporter_contact": self.contact_input.text().strip() or None,
            "priority": self.priority_combo.currentData(),
            "status": self.status_combo.currentData(),
            "assigned_technician_id": self.tech_combo.currentData(),
            "total_labor_cost": self.labor_cost_spin.value(),
            "total_parts_cost": self.parts_cost_spin.value(),
            "failure_description": desc,
            "symptoms": self.symptoms_input.text().strip() or None,
            "diagnosis": self.diagnosis_input.toPlainText().strip() or None,
            "corrective_action": self.action_input.toPlainText().strip() or None,
        }

        user = auth_service.current_user
        try:
            with get_db() as db:
                if self.work_order:
                    work_order_service.update_work_order(db, user, self.work_order.id, data)
                else:
                    work_order_service.create_work_order(db, user, data)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))
