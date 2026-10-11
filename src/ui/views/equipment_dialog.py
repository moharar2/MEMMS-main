"""
Enterprise Medical Equipment Dialog for creation and updates.
Organized in a structured 2-column grid layout with clean validation and full bilingual support.
Zero emojis.
"""
from typing import Optional
from datetime import date
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox, QTextEdit,
    QPushButton, QMessageBox, QFrame, QScrollArea, QWidget
)
from PySide6.QtCore import QDate, Qt
from src.core.i18n import tr, i18n
from src.core.database import get_db
from src.services.equipment_service import equipment_service
from src.services.hospital_service import hospital_service
from src.services.vendor_service import vendor_service
from src.services.auth_service import auth_service
from src.models.equipment import Equipment
from src.ui.theme.icons import icon


class EquipmentDialog(QDialog):
    CATEGORIES = [
        "أجهزة عناية وتنفس",
        "أجهزة مراقبة ودعم الحياة",
        "أجهزة أشعة وتصوير طبي",
        "أجهزة عمليات وجراحة",
        "أجهزة مناظير جهاز هضمي وجراحي",
        "أجهزة قلب وقسطرة قلبية",
        "أجهزة مختبرات وتحاليل طبية",
        "أجهزة غسيل كلى وتصفية دم",
        "أجهزة حضانات ورعاية أطفال",
        "أجهزة علاج طبيعي وتأهيل",
        "أجهزة تعقيم ومكافحة عدوى",
        "أجهزة طبية عامة وأخرى"
    ]

    def __init__(self, equipment: Optional[Equipment] = None, parent=None):
        super().__init__(parent)
        self.equipment = equipment
        action_title = tr("common.edit") if equipment else tr("equipment.add_button")
        self.setWindowTitle(f"{action_title} — MEMMS")
        self.setMinimumSize(780, 640)
        self.setModal(True)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(16)

        # Header Title
        title_lbl = QLabel(action_title)
        title_lbl.setStyleSheet("font-size: 18px; font-weight: 800; color: #0F172A;")
        main_layout.addWidget(title_lbl)

        # Scrollable form container
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(18)

        # === Section 1: Equipment Identification ===
        sec1_title = QLabel(tr("equipment.tabs.basic_info"))
        sec1_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #0F766E; border-bottom: 1px solid #E2E8F0; padding-bottom: 4px;")
        form_layout.addWidget(sec1_title)

        grid1 = QGridLayout()
        grid1.setHorizontalSpacing(16)
        grid1.setVerticalSpacing(12)

        self.asset_no_input = QLineEdit()
        self.serial_no_input = QLineEdit()
        self.inv_no_input = QLineEdit()
        self.name_ar_input = QLineEdit()
        self.name_en_input = QLineEdit()
        self.model_input = QLineEdit()
        self.category_combo = QComboBox()
        for cat in self.CATEGORIES:
            self.category_combo.addItem(cat, cat)

        self._add_field(grid1, 0, 0, tr("equipment.asset_id") + " *", self.asset_no_input)
        self._add_field(grid1, 0, 1, tr("equipment.serial_number") + " *", self.serial_no_input)
        self._add_field(grid1, 1, 0, tr("equipment.name_ar") + " *", self.name_ar_input)
        self._add_field(grid1, 1, 1, tr("equipment.name_en"), self.name_en_input)
        self._add_field(grid1, 2, 0, tr("equipment.category"), self.category_combo)
        self._add_field(grid1, 2, 1, tr("equipment.model"), self.model_input)
        self._add_field(grid1, 3, 0, tr("equipment.inventory_number"), self.inv_no_input)
        form_layout.addLayout(grid1)

        # === Section 2: Location & Vendors ===
        sec2_title = QLabel(tr("equipment.tabs.location_vendor"))
        sec2_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #0F766E; border-bottom: 1px solid #E2E8F0; padding-bottom: 4px; margin-top: 10px;")
        form_layout.addWidget(sec2_title)

        grid2 = QGridLayout()
        grid2.setHorizontalSpacing(16)
        grid2.setVerticalSpacing(12)

        self.dept_combo = QComboBox()
        self.dept_combo.currentIndexChanged.connect(self._on_dept_changed)
        self.loc_combo = QComboBox()
        self.manufacturer_combo = QComboBox()
        self.supplier_combo = QComboBox()
        self.agent_combo = QComboBox()
        self.engineer_combo = QComboBox()

        self._add_field(grid2, 0, 0, tr("equipment.department") + " *", self.dept_combo)
        self._add_field(grid2, 0, 1, tr("equipment.location"), self.loc_combo)
        self._add_field(grid2, 1, 0, tr("equipment.manufacturer"), self.manufacturer_combo)
        self._add_field(grid2, 1, 1, tr("equipment.supplier"), self.supplier_combo)
        self._add_field(grid2, 2, 0, tr("equipment.agent"), self.agent_combo)
        self._add_field(grid2, 2, 1, "مهندس الدعم المعتمد", self.engineer_combo)
        form_layout.addLayout(grid2)

        # === Section 3: Status, Warranty & Financials ===
        sec3_title = QLabel(tr("equipment.tabs.status_financial"))
        sec3_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #0F766E; border-bottom: 1px solid #E2E8F0; padding-bottom: 4px; margin-top: 10px;")
        form_layout.addWidget(sec3_title)

        grid3 = QGridLayout()
        grid3.setHorizontalSpacing(16)
        grid3.setVerticalSpacing(12)

        self.status_combo = QComboBox()
        for st in ["operational", "under_maintenance", "out_of_service", "standby", "scrapped"]:
            self.status_combo.addItem(tr(f"status.{st}"), st)

        self.risk_combo = QComboBox()
        for rk in ["high", "medium", "low"]:
            self.risk_combo.addItem(tr(f"risk.{rk}"), rk)

        self.criticality_combo = QComboBox()
        for cr in ["critical", "semi_critical", "non_critical"]:
            self.criticality_combo.addItem(tr(f"criticality.{cr}"), cr)

        self.purchase_date_input = QDateEdit()
        self.purchase_date_input.setCalendarPopup(True)
        self.purchase_date_input.setDate(QDate.currentDate())

        self.install_date_input = QDateEdit()
        self.install_date_input.setCalendarPopup(True)
        self.install_date_input.setDate(QDate.currentDate())

        self.warranty_expiry_input = QDateEdit()
        self.warranty_expiry_input.setCalendarPopup(True)
        self.warranty_expiry_input.setDate(QDate.currentDate().addYears(1))

        self.price_input = QDoubleSpinBox()
        self.price_input.setRange(0, 100000000)
        self.price_input.setSuffix(" SAR")

        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(70)

        self._add_field(grid3, 0, 0, tr("equipment.status"), self.status_combo)
        self._add_field(grid3, 0, 1, tr("equipment.risk_level"), self.risk_combo)
        self._add_field(grid3, 1, 0, tr("equipment.criticality"), self.criticality_combo)
        self._add_field(grid3, 1, 1, tr("equipment.purchase_price"), self.price_input)
        self._add_field(grid3, 2, 0, tr("equipment.purchase_date"), self.purchase_date_input)
        self._add_field(grid3, 2, 1, tr("equipment.warranty_expiry"), self.warranty_expiry_input)
        self._add_field(grid3, 3, 0, tr("equipment.install_date"), self.install_date_input)

        # Notes full row
        notes_box = QVBoxLayout()
        notes_lbl = QLabel(tr("common.notes"))
        notes_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #475569;")
        notes_box.addWidget(notes_lbl)
        notes_box.addWidget(self.notes_input)
        grid3.addLayout(notes_box, 4, 0, 1, 2)

        form_layout.addLayout(grid3)

        scroll.setWidget(form_widget)
        main_layout.addWidget(scroll, stretch=1)

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.addStretch()

        cancel_btn = QPushButton(tr("common.cancel"))
        cancel_btn.setProperty("variant", "secondary")
        cancel_btn.setIcon(icon("cancel", color="#64748B", size=14))
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton(tr("common.save"))
        save_btn.setIcon(icon("save", color="#FFFFFF", size=14))
        save_btn.clicked.connect(self._save)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        main_layout.addLayout(btn_layout)

        self._load_dropdowns()
        if self.equipment:
            self._load_data()

    def _add_field(self, grid: QGridLayout, row: int, col: int, label_text: str, widget: QWidget):
        box = QVBoxLayout()
        box.setSpacing(4)
        lbl = QLabel(label_text)
        lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #475569;")
        box.addWidget(lbl)
        box.addWidget(widget)
        grid.addLayout(box, row, col)

    def _load_dropdowns(self):
        with get_db() as db:
            # Departments
            depts = hospital_service.get_departments(db)
            self.dept_combo.clear()
            for d in depts:
                dept_name = d.name_en if not i18n.is_rtl() and d.name_en else d.name_ar
                self.dept_combo.addItem(f"{dept_name} ({d.code})", d.id)

            # Vendors
            vendors = vendor_service.get_vendors(db)
            self.manufacturer_combo.clear()
            self.supplier_combo.clear()
            self.agent_combo.clear()

            none_text = "— None —" if not i18n.is_rtl() else "— غير محدد —"
            self.manufacturer_combo.addItem(none_text, None)
            self.supplier_combo.addItem(none_text, None)
            self.agent_combo.addItem(none_text, None)

            for v in vendors:
                self.manufacturer_combo.addItem(f"{v.name} ({v.vendor_type})", v.id)
                self.supplier_combo.addItem(f"{v.name} ({v.vendor_type})", v.id)
                self.agent_combo.addItem(f"{v.name} ({v.vendor_type})", v.id)

            # Engineers
            engineers = vendor_service.get_all_engineers(db)
            self.engineer_combo.clear()
            self.engineer_combo.addItem(none_text, None)
            for eng in engineers:
                v_name = eng.vendor.name if eng.vendor else ""
                self.engineer_combo.addItem(f"{eng.name} — {v_name}", eng.id)

            # Extra categories from database if any
            try:
                db_cats = [c[0] for c in db.query(Equipment.category).distinct().filter(Equipment.category.isnot(None)).all() if c[0]]
                for c in db_cats:
                    if self.category_combo.findData(c) < 0:
                        self.category_combo.addItem(c, c)
            except Exception:
                pass

    def _on_dept_changed(self):
        dept_id = self.dept_combo.currentData()
        self.loc_combo.clear()
        none_text = "— None —" if not i18n.is_rtl() else "— بدون غرفة —"
        self.loc_combo.addItem(none_text, None)
        if dept_id:
            with get_db() as db:
                locs = hospital_service.get_locations(db, dept_id)
                for loc in locs:
                    self.loc_combo.addItem(f"{loc.room_name} ({loc.room_number})", loc.id)

    def _load_data(self):
        eq = self.equipment
        self.asset_no_input.setText(eq.asset_number)
        self.serial_no_input.setText(eq.serial_number)
        self.inv_no_input.setText(eq.inventory_number or "")
        self.name_ar_input.setText(eq.name_ar)
        self.name_en_input.setText(eq.name_en or "")
        self.model_input.setText(eq.model or "")

        if eq.category and self.category_combo.findData(eq.category) < 0:
            self.category_combo.addItem(eq.category, eq.category)
        idx = self.category_combo.findData(eq.category)
        if idx >= 0:
            self.category_combo.setCurrentIndex(idx)

        d_idx = self.dept_combo.findData(eq.department_id)
        if d_idx >= 0:
            self.dept_combo.setCurrentIndex(d_idx)
        self._on_dept_changed()
        l_idx = self.loc_combo.findData(eq.location_id)
        if l_idx >= 0:
            self.loc_combo.setCurrentIndex(l_idx)

        m_idx = self.manufacturer_combo.findData(eq.manufacturer_id)
        if m_idx >= 0:
            self.manufacturer_combo.setCurrentIndex(m_idx)
        s_idx = self.supplier_combo.findData(eq.supplier_id)
        if s_idx >= 0:
            self.supplier_combo.setCurrentIndex(s_idx)
        a_idx = self.agent_combo.findData(eq.agent_id)
        if a_idx >= 0:
            self.agent_combo.setCurrentIndex(a_idx)
        if hasattr(eq, "assigned_engineer_id") and eq.assigned_engineer_id:
            e_idx = self.engineer_combo.findData(eq.assigned_engineer_id)
            if e_idx >= 0:
                self.engineer_combo.setCurrentIndex(e_idx)

        st_idx = self.status_combo.findData(eq.status)
        if st_idx >= 0:
            self.status_combo.setCurrentIndex(st_idx)
        rk_idx = self.risk_combo.findData(eq.risk_level)
        if rk_idx >= 0:
            self.risk_combo.setCurrentIndex(rk_idx)
        cr_idx = self.criticality_combo.findData(eq.criticality)
        if cr_idx >= 0:
            self.criticality_combo.setCurrentIndex(cr_idx)

        if eq.purchase_date:
            self.purchase_date_input.setDate(QDate(eq.purchase_date.year, eq.purchase_date.month, eq.purchase_date.day))
        if eq.installation_date:
            self.install_date_input.setDate(QDate(eq.installation_date.year, eq.installation_date.month, eq.installation_date.day))
        if eq.warranty_expiry_date:
            self.warranty_expiry_input.setDate(QDate(eq.warranty_expiry_date.year, eq.warranty_expiry_date.month, eq.warranty_expiry_date.day))

        self.price_input.setValue(eq.purchase_price or 0.0)
        self.notes_input.setPlainText(eq.notes or "")

    def _save(self):
        asset_no = self.asset_no_input.text().strip()
        serial_no = self.serial_no_input.text().strip()
        name_ar = self.name_ar_input.text().strip()
        name_en = self.name_en_input.text().strip() or name_ar
        dept_id = self.dept_combo.currentData()

        if not asset_no or not serial_no or not name_ar or not dept_id:
            QMessageBox.warning(self, tr("dialog.confirm_title"), tr("dialog.validation_error"))
            return

        p_date = self.purchase_date_input.date()
        i_date = self.install_date_input.date()
        w_date = self.warranty_expiry_input.date()

        data = {
            "asset_number": asset_no,
            "serial_number": serial_no,
            "inventory_number": self.inv_no_input.text().strip(),
            "name_ar": name_ar,
            "name_en": name_en,
            "model": self.model_input.text().strip(),
            "category": self.category_combo.currentData() or "General / Other",
            "department_id": dept_id,
            "location_id": self.loc_combo.currentData(),
            "manufacturer_id": self.manufacturer_combo.currentData(),
            "supplier_id": self.supplier_combo.currentData(),
            "agent_id": self.agent_combo.currentData(),
            "assigned_engineer_id": self.engineer_combo.currentData(),
            "status": self.status_combo.currentData(),
            "risk_level": self.risk_combo.currentData(),
            "criticality": self.criticality_combo.currentData(),
            "purchase_date": date(p_date.year(), p_date.month(), p_date.day()),
            "installation_date": date(i_date.year(), i_date.month(), i_date.day()),
            "warranty_expiry_date": date(w_date.year(), w_date.month(), w_date.day()),
            "purchase_price": self.price_input.value(),
            "notes": self.notes_input.toPlainText().strip()
        }

        user = auth_service.current_user
        try:
            with get_db() as db:
                if self.equipment:
                    equipment_service.update_equipment(db, user, self.equipment.id, data)
                else:
                    equipment_service.create_equipment(db, user, data)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, tr("common.error"), str(e))
