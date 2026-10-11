"""
Dialog for managing Vendor Support Engineers & Biomedical Specialists.
Pure Arabic, RTL, zero emojis.
"""
from typing import Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QMessageBox, QFrame, QLineEdit,
    QComboBox, QGridLayout
)
from PySide6.QtCore import Qt
from src.core.database import get_db
from src.services.vendor_service import vendor_service
from src.services.auth_service import auth_service
from src.models.vendor import Vendor, VendorEngineer
from src.ui.theme.icons import icon


class EngineerFormDialog(QDialog):
    def __init__(self, engineer: Optional[VendorEngineer] = None, parent=None):
        super().__init__(parent)
        self.engineer = engineer
        action_title = "تعديل بيانات مهندس الدعم" if engineer else "إضافة مهندس دعم فني جديد"
        self.setWindowTitle(f"{action_title} — MEMMS")
        self.setFixedSize(460, 360)
        self.setModal(True)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        grid = QGridLayout()
        grid.setSpacing(10)

        self.name_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.email_input = QLineEdit()
        self.spec_input = QLineEdit()
        self.status_combo = QComboBox()
        self.status_combo.addItem("نشط ومتاح للخدمة", "active")
        self.status_combo.addItem("غير متاح / معطل", "inactive")

        grid.addWidget(QLabel("اسم المهندس *:"), 0, 0)
        grid.addWidget(self.name_input, 0, 1)

        grid.addWidget(QLabel("رقم الهاتف:"), 1, 0)
        grid.addWidget(self.phone_input, 1, 1)

        grid.addWidget(QLabel("البريد الإلكتروني:"), 2, 0)
        grid.addWidget(self.email_input, 2, 1)

        grid.addWidget(QLabel("التخصص / النظم الطبية:"), 3, 0)
        grid.addWidget(self.spec_input, 3, 1)

        grid.addWidget(QLabel("حالة العمل:"), 4, 0)
        grid.addWidget(self.status_combo, 4, 1)

        layout.addLayout(grid)
        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = QPushButton("إلغاء")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("حفظ")
        save_btn.setObjectName("primaryBtn")
        save_btn.clicked.connect(self._save)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

        if self.engineer:
            self.name_input.setText(self.engineer.name or "")
            self.phone_input.setText(self.engineer.phone or "")
            self.email_input.setText(self.engineer.email or "")
            self.spec_input.setText(self.engineer.specialization or "")
            idx = self.status_combo.findData(self.engineer.status)
            if idx >= 0:
                self.status_combo.setCurrentIndex(idx)

    def _save(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "خطأ في البيانات", "يرجى كتابة اسم المهندس.")
            return

        self.result_data = {
            "name": name,
            "phone": self.phone_input.text().strip() or None,
            "email": self.email_input.text().strip() or None,
            "specialization": self.spec_input.text().strip() or None,
            "status": self.status_combo.currentData()
        }
        self.accept()


class VendorEngineersDialog(QDialog):
    def __init__(self, vendor: Vendor, parent=None):
        super().__init__(parent)
        self.vendor = vendor
        self.setWindowTitle(f"مهندسو الدعم الفني — {vendor.name}")
        self.resize(720, 480)
        self.setModal(True)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        # Header
        header = QFrame()
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(0, 0, 0, 0)
        title_lbl = QLabel(f"مهندسو وممثلو الدعم المعتمدون: {vendor.name}")
        title_lbl.setStyleSheet("font-size: 16px; font-weight: 700; color: #0F172A;")
        h_layout.addWidget(title_lbl)
        h_layout.addStretch()

        add_btn = QPushButton("+ إضافة مهندس دعم")
        add_btn.setObjectName("primaryBtn")
        add_btn.setIcon(icon("add", color="#FFFFFF", size=14))
        add_btn.clicked.connect(self._on_add)
        h_layout.addWidget(add_btn)
        layout.addWidget(header)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "اسم المهندس",
            "التخصص",
            "رقم الهاتف",
            "البريد الإلكتروني",
            "الحالة"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)

        # Action bar
        btn_layout = QHBoxLayout()
        edit_btn = QPushButton("تعديل")
        edit_btn.setIcon(icon("edit", color="#0F766E", size=14))
        edit_btn.clicked.connect(self._on_edit)
        btn_layout.addWidget(edit_btn)

        del_btn = QPushButton("حذف / تعطيل")
        del_btn.setIcon(icon("delete", color="#DC2626", size=14))
        del_btn.clicked.connect(self._on_delete)
        btn_layout.addWidget(del_btn)

        btn_layout.addStretch()
        close_btn = QPushButton("إغلاق")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

        self._load_engineers()

    def _load_engineers(self):
        with get_db() as db:
            engineers = vendor_service.get_vendor_engineers(db, self.vendor.id)
            self.engineers = engineers
            self.table.setRowCount(len(engineers))
            for r, eng in enumerate(engineers):
                self.table.setItem(r, 0, QTableWidgetItem(eng.name))
                self.table.setItem(r, 1, QTableWidgetItem(eng.specialization or "عام"))
                self.table.setItem(r, 2, QTableWidgetItem(eng.phone or "—"))
                self.table.setItem(r, 3, QTableWidgetItem(eng.email or "—"))
                status_str = "نشط" if eng.status == "active" else "معطل"
                self.table.setItem(r, 4, QTableWidgetItem(status_str))

    def _selected_engineer(self) -> Optional[VendorEngineer]:
        row = self.table.currentRow()
        if 0 <= row < len(self.engineers):
            return self.engineers[row]
        return None

    def _on_add(self):
        dlg = EngineerFormDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.result_data
            user = auth_service.current_user
            with get_db() as db:
                vendor_service.add_engineer(db, user, self.vendor.id, data)
            self._load_engineers()

    def _on_edit(self):
        eng = self._selected_engineer()
        if not eng:
            QMessageBox.information(self, "تنبيه", "يرجى اختيار مهندس من الجدول للتعديل.")
            return
        dlg = EngineerFormDialog(engineer=eng, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.result_data
            user = auth_service.current_user
            with get_db() as db:
                vendor_service.update_engineer(db, user, eng.id, data)
            self._load_engineers()

    def _on_delete(self):
        eng = self._selected_engineer()
        if not eng:
            QMessageBox.information(self, "تنبيه", "يرجى اختيار مهندس من الجدول.")
            return
        ans = QMessageBox.question(
            self,
            "تأكيد الحذف",
            f"هل أنت متأكد من رغبتك في حذف أو تعطيل المهندس '{eng.name}'؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if ans == QMessageBox.StandardButton.Yes:
            user = auth_service.current_user
            with get_db() as db:
                vendor_service.delete_engineer(db, user, eng.id)
            self._load_engineers()
