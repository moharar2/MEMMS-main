"""
Vendors and Suppliers View: Directory of certified manufacturers, suppliers, and agents.
Pure Arabic, RTL, zero emojis.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidgetItem, QMessageBox, QLabel, QFrame, QHeaderView
)
from PySide6.QtCore import Qt
from src.core.i18n import tr
from src.core.database import get_db
from src.services.vendor_service import vendor_service
from src.services.auth_service import auth_service
from src.ui.theme.icons import icon
from src.ui.components.data_table import DataTable
from src.ui.components.confirm_dialog import confirm_action
from src.ui.components.action_button import ActionButton, create_actions_cell
from src.ui.views.vendor_dialog import VendorDialog
from src.ui.views.vendor_engineers_dialog import VendorEngineersDialog


class VendorsView(QWidget):
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
        self.title_lbl = QLabel("الشركات المصنعة والموردين")
        self.title_lbl.setStyleSheet("font-size: 18px; font-weight: 800; color: #0F172A;")

        self.subtitle_lbl = QLabel("دليل الشركات المصنعة، الموردين المعتمدين، ووكلاء صيانة الأجهزة الطبية")
        self.subtitle_lbl.setStyleSheet("font-size: 12px; color: #64748B; font-weight: 500;")

        titles_box.addWidget(self.title_lbl)
        titles_box.addWidget(self.subtitle_lbl)
        h_layout.addLayout(titles_box)
        h_layout.addStretch()

        layout.addWidget(header_frame)

        headers = [
            "اسم الشركة / المورد",
            "نوع النشاط / التصنيف",
            "الشخص المسؤول",
            "رقم الهاتف",
            "البريد الإلكتروني",
            "الإجراءات"
        ]

        self.table_widget = DataTable()
        self.table_widget.set_search_placeholder("بحث باسم الشركة، مسؤول التواصل، أو الهاتف...")
        self.table_widget.set_headers(headers)
        self.table_widget.set_add_button_text("+ إضافة مورد")
        self.table_widget.search_changed.connect(lambda txt: self.load_data())
        self.table_widget.refresh_requested.connect(self.load_data)
        self.table_widget.add_clicked.connect(self._on_add)
        # 0: Name, 1: Type, 2: Contact, 3: Phone, 4: Email, 5: Actions
        self.table_widget.set_column_widths([200, 140, 150, 120, 180, 110], stretch_cols=[0, 2, 4])
        self.table_widget.table.verticalHeader().setDefaultSectionSize(38)

        layout.addWidget(self.table_widget, stretch=1)
        self.load_data()

    def load_data(self):
        search_txt = self.table_widget.search_input.text().strip().lower()

        with get_db() as db:
            vendors = vendor_service.get_vendors(db)

            if search_txt:
                vendors = [
                    v for v in vendors
                    if search_txt in v.name.lower()
                    or search_txt in (v.contact_person or "").lower()
                    or search_txt in (v.phone or "").lower()
                ]

            tbl = self.table_widget.table
            tbl.setRowCount(len(vendors))

            type_map = {
                "manufacturer": "شركة مصنعة",
                "supplier": "مورد معتمد",
                "agent": "وكيل معتمد وموزع",
                "service_agent": "وكيل صيانة وخدمة",
                "service_provider": "مزود خدمات وصيانة",
                "both": "مصنع ومورد"
            }

            for row_idx, v in enumerate(vendors):
                it_name = QTableWidgetItem(v.name)
                it_name.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                tbl.setItem(row_idx, 0, it_name)

                it_type = QTableWidgetItem(type_map.get(v.vendor_type, v.vendor_type or "مورد"))
                it_type.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                tbl.setItem(row_idx, 1, it_type)

                it_cp = QTableWidgetItem(v.contact_person or "—")
                it_cp.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                tbl.setItem(row_idx, 2, it_cp)

                it_ph = QTableWidgetItem(v.phone or "—")
                it_ph.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                tbl.setItem(row_idx, 3, it_ph)

                it_em = QTableWidgetItem(v.email or "—")
                it_em.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                tbl.setItem(row_idx, 4, it_em)

                # Action buttons (Engineers, Edit, Delete)
                eng_btn = ActionButton(
                    action_type="view",
                    tooltip="مهندسو الدعم الفني",
                    callback=lambda _, item_id=v.id: self._on_manage_engineers(item_id)
                )
                edit_btn = ActionButton(
                    action_type="edit",
                    tooltip="تعديل بيانات الشركة",
                    callback=lambda _, item_id=v.id: self._on_edit(item_id)
                )
                del_btn = ActionButton(
                    action_type="delete",
                    tooltip="حذف الشركة",
                    callback=lambda _, item_id=v.id: self._on_delete(item_id)
                )

                actions_widget = create_actions_cell(eng_btn, edit_btn, del_btn)
                tbl.setCellWidget(row_idx, 5, actions_widget)

            self.table_widget.set_record_count(len(vendors), len(vendors))

    def _on_manage_engineers(self, vendor_id: int):
        with get_db() as db:
            v = vendor_service.get_vendor_by_id(db, vendor_id)
            if not v:
                return
            dlg = VendorEngineersDialog(vendor=v, parent=self)
            dlg.exec()

    def _on_add(self):
        dlg = VendorDialog(parent=self)
        if dlg.exec() == VendorDialog.DialogCode.Accepted:
            self.load_data()

    def _on_edit(self, vendor_id: int):
        with get_db() as db:
            v = vendor_service.get_vendor_by_id(db, vendor_id)
            if not v:
                return
            dlg = VendorDialog(vendor=v, parent=self)
            if dlg.exec() == VendorDialog.DialogCode.Accepted:
                self.load_data()

    def _on_delete(self, vendor_id: int):
        if confirm_action(self, "تأكيد الحذف", "هل أنت متأكد من رغبتك في حذف بيانات هذه الشركة؟"):
            user = auth_service.current_user
            try:
                with get_db() as db:
                    vendor_service.delete_vendor(db, user, vendor_id)
                self.load_data()
            except Exception as e:
                QMessageBox.critical(self, "خطأ", str(e))

    def retranslate_ui(self):
        self.load_data()
