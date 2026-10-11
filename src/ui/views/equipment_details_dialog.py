"""
Equipment Details inspection dialog for comprehensive asset lifecycle review.
Pure Arabic, RTL, zero emojis. Complete tabs for Work Orders, PM, Parts, Transfers,
Operation & Service Manuals (PDF), Accessories & Costs, and Receiving & Commissioning.
"""
import os
import subprocess
import sys
from typing import Union, Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QPushButton, QFrame, QGridLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QUrl, QSizeF, QMarginsF
from PySide6.QtGui import QDesktopServices, QTextDocument, QPageSize, QPageLayout, QFont
from PySide6.QtPrintSupport import QPrinter, QPrintPreviewDialog
from sqlalchemy.orm import joinedload
from src.core.i18n import tr
from src.core.database import get_db
from src.models.equipment import Equipment, EquipmentTransfer, EquipmentAccessory, EquipmentReceiving
from src.models.work_order import WorkOrder, WorkOrderPart
from src.models.preventive import PMSchedule
from src.models.attachment import Attachment
from src.services.attachment_service import attachment_service
from src.services.equipment_service import equipment_service
from src.services.report_service import report_service
from src.services.auth_service import auth_service
from src.ui.theme.icons import icon
from src.ui.components.status_badge import StatusBadge
from src.ui.views.equipment_accessory_dialog import EquipmentAccessoryDialog
from src.ui.views.equipment_receiving_dialog import EquipmentReceivingDialog


class EquipmentDetailsDialog(QDialog):
    edit_requested = Signal(int)
    transfer_requested = Signal(int)

    def __init__(self, equipment: Union[Equipment, int], parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        eq_id = equipment if isinstance(equipment, int) else getattr(equipment, "id", None)

        self.equipment = None
        if eq_id:
            with get_db() as db:
                self.equipment = db.query(Equipment).options(
                    joinedload(Equipment.department),
                    joinedload(Equipment.location),
                    joinedload(Equipment.manufacturer),
                    joinedload(Equipment.supplier),
                    joinedload(Equipment.agent),
                    joinedload(Equipment.assigned_engineer)
                ).filter_by(id=eq_id).first()

        if self.equipment is None and isinstance(equipment, Equipment):
            self.equipment = equipment

        equipment = self.equipment
        self.setWindowTitle(f"بطاقة الجهاز الطبي — {equipment.asset_number if equipment else ''}")
        self.setMinimumSize(920, 680)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 16)
        layout.setSpacing(14)

        if not equipment:
            layout.addWidget(QLabel("لم يتم العثور على بيانات الجهاز."))
            return

        # 1. Header Banner
        header_card = QFrame()
        header_card.setStyleSheet("""
            QFrame {
                background-color: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                padding: 12px 16px;
            }
        """)
        h_layout = QHBoxLayout(header_card)
        h_layout.setContentsMargins(0, 0, 0, 0)

        title_box = QVBoxLayout()
        title_box.setSpacing(4)
        eq_name = equipment.name_ar or equipment.name_en or "جهاز طبي"
        name_lbl = QLabel(eq_name)
        name_lbl.setStyleSheet("font-size: 18px; font-weight: 800; color: #0F172A;")

        sub_lbl = QLabel(f"{equipment.category or 'عام'} • {equipment.model or 'قياسي'} • الرقم التسلسلي: {equipment.serial_number}")
        sub_lbl.setStyleSheet("font-size: 12px; color: #64748B; font-weight: 500;")

        title_box.addWidget(name_lbl)
        title_box.addWidget(sub_lbl)
        h_layout.addLayout(title_box)
        h_layout.addStretch()

        badges_box = QVBoxLayout()
        badges_box.setSpacing(6)
        badges_box.setAlignment(Qt.AlignmentFlag.AlignRight)
        status_badge = StatusBadge(equipment.status)
        risk_badge = StatusBadge(f"risk_{equipment.risk_level}")
        badges_box.addWidget(status_badge)
        badges_box.addWidget(risk_badge)
        h_layout.addLayout(badges_box)

        layout.addWidget(header_card)

        # 2. Tabs Widget
        self.tabs = QTabWidget()

        # Tab 1: General & Location
        self._build_tab_general()

        # Tab 2: Lifecycle & Financials
        self._build_tab_lifecycle()

        # Tab 3: Manuals & PDF Attachments (NEW)
        self._build_tab_manuals()

        # Tab 4: Accessories & Costs (NEW)
        self._build_tab_accessories()

        # Tab 5: Receiving & Commissioning (NEW)
        self._build_tab_receiving()

        # Tab 6: Work Orders
        self._build_tab_work_orders()

        # Tab 7: PM
        self._build_tab_pm()

        # Tab 8: Consumed Spare Parts
        self._build_tab_parts()

        # Tab 9: Transfers
        self._build_tab_transfers()

        layout.addWidget(self.tabs, stretch=1)

        # 3. Actions Bar
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        transfer_btn = QPushButton("نقل الجهاز")
        transfer_btn.setProperty("variant", "secondary")
        transfer_btn.setIcon(icon("transfer", color="#0F766E", size=14))
        transfer_btn.clicked.connect(self._on_transfer)
        btn_layout.addWidget(transfer_btn)

        edit_btn = QPushButton("تعديل البيانات الأساسية")
        edit_btn.setProperty("variant", "secondary")
        edit_btn.setIcon(icon("edit", color="#0F766E", size=14))
        edit_btn.clicked.connect(self._on_edit)
        btn_layout.addWidget(edit_btn)

        report_btn = QPushButton("تقرير صيانة الجهاز (طباعة / PDF)")
        report_btn.setStyleSheet("""
            QPushButton {
                background-color: #0284C7;
                color: #FFFFFF;
                font-weight: 700;
                font-size: 12px;
                padding: 6px 14px;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #0369A1; }
        """)
        report_btn.setIcon(icon("print", color="#FFFFFF", size=14))
        report_btn.clicked.connect(self._on_export_report)
        btn_layout.addWidget(report_btn)

        btn_layout.addStretch()

        close_btn = QPushButton("إغلاق")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def _add_detail_row(self, layout: QGridLayout, row: int, label_text: str, val_text: str):
        lbl = QLabel(label_text)
        lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #64748B;")
        val = QLabel(val_text)
        val.setStyleSheet("font-size: 13px; font-weight: 500; color: #0F172A;")
        val.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(lbl, row, 0)
        layout.addWidget(val, row, 1)

    # ── Tab 1: General & Location ────────────────────────────────────────────
    def _build_tab_general(self):
        eq = self.equipment
        tab_general = QWidget()
        g_layout = QGridLayout(tab_general)
        g_layout.setContentsMargins(18, 18, 18, 18)
        g_layout.setHorizontalSpacing(24)
        g_layout.setVerticalSpacing(12)

        self._add_detail_row(g_layout, 0, "رقم الأصل:", eq.asset_number)
        self._add_detail_row(g_layout, 1, "الرقم التسلسلي:", eq.serial_number)
        self._add_detail_row(g_layout, 2, "رقم الجرد/المستودع:", eq.inventory_number or "—")
        self._add_detail_row(g_layout, 3, "التصنيف:", eq.category or "—")
        self._add_detail_row(g_layout, 4, "الموديل:", eq.model or "—")

        dept_name = eq.department.name_ar if eq.department else "—"
        self._add_detail_row(g_layout, 5, "القسم:", dept_name)
        room_name = eq.location.room_name if eq.location else "—"
        self._add_detail_row(g_layout, 6, "الموقع / الغرفة:", room_name)

        manuf_name = eq.manufacturer.name if eq.manufacturer else "—"
        self._add_detail_row(g_layout, 7, "الشركة المصنعة:", manuf_name)
        supp_name = eq.supplier.name if eq.supplier else "—"
        self._add_detail_row(g_layout, 8, "المورد:", supp_name)

        agent_name = eq.agent.name if eq.agent else "—"
        self._add_detail_row(g_layout, 9, "الوكيل المعتمد:", agent_name)

        eng_str = f"{eq.assigned_engineer.name} ({eq.assigned_engineer.phone or '—'})" if eq.assigned_engineer else "—"
        self._add_detail_row(g_layout, 10, "مهندس الدعم المسؤول:", eng_str)

        self.tabs.addTab(tab_general, "نظرة عامة والجهات")

    # ── Tab 2: Lifecycle & Financials ────────────────────────────────────────
    def _build_tab_lifecycle(self):
        eq = self.equipment
        tab_life = QWidget()
        l_layout = QGridLayout(tab_life)
        l_layout.setContentsMargins(18, 18, 18, 18)
        l_layout.setHorizontalSpacing(24)
        l_layout.setVerticalSpacing(14)

        self._add_detail_row(l_layout, 0, "تاريخ الشراء:", str(eq.purchase_date or "—"))
        self._add_detail_row(l_layout, 1, "تاريخ التركيب والتشغيل:", str(eq.installation_date or "—"))
        self._add_detail_row(l_layout, 2, "انتهاء فترة الضمان:", str(eq.warranty_expiry_date or "—"))
        price_str = f"{eq.purchase_price:,.2f} ر.س" if eq.purchase_price else "—"
        self._add_detail_row(l_layout, 3, "سعر الشراء الأساسي:", price_str)
        self._add_detail_row(l_layout, 4, "درجة الحرجية السريرية:", tr(f"criticality.{eq.criticality}"))
        self._add_detail_row(l_layout, 5, "ملاحظات:", eq.notes or "—")

        self.tabs.addTab(tab_life, "الضمان والبيانات المالية")

    # ── Tab 3: Manuals & PDF Attachments ─────────────────────────────────────
    def _build_tab_manuals(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # Toolbar
        bar = QHBoxLayout()
        bar.setSpacing(8)

        add_op_btn = QPushButton("+ رفع دليل التشغيل (Operation Manual)")
        add_op_btn.setProperty("variant", "secondary")
        add_op_btn.setIcon(icon("upload", color="#0F766E", size=14))
        add_op_btn.clicked.connect(lambda: self._upload_manual("operation_manual"))
        bar.addWidget(add_op_btn)

        add_srv_btn = QPushButton("+ رفع دليل الصيانة (Service Manual)")
        add_srv_btn.setProperty("variant", "secondary")
        add_srv_btn.setIcon(icon("upload", color="#0F766E", size=14))
        add_srv_btn.clicked.connect(lambda: self._upload_manual("service_manual"))
        bar.addWidget(add_srv_btn)

        add_gen_btn = QPushButton("+ رفع ملف آخر")
        add_gen_btn.setProperty("variant", "secondary")
        add_gen_btn.setIcon(icon("upload", color="#0F766E", size=14))
        add_gen_btn.clicked.connect(lambda: self._upload_manual("general"))
        bar.addWidget(add_gen_btn)

        bar.addStretch()

        open_btn = QPushButton("فتح الملف")
        open_btn.setIcon(icon("reports", color="#0F766E", size=14))
        open_btn.clicked.connect(self._open_selected_manual)
        bar.addWidget(open_btn)

        dl_btn = QPushButton("تنزيل نسخة")
        dl_btn.setIcon(icon("download", color="#0F766E", size=14))
        dl_btn.clicked.connect(self._download_selected_manual)
        bar.addWidget(dl_btn)

        del_btn = QPushButton("حذف")
        del_btn.setIcon(icon("delete", color="#DC2626", size=14))
        del_btn.clicked.connect(self._delete_selected_manual)
        bar.addWidget(del_btn)

        layout.addLayout(bar)

        self.manuals_table = QTableWidget()
        self.manuals_table.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.manuals_table.setColumnCount(5)
        self.manuals_table.setHorizontalHeaderLabels([
            "نوع المرفق",
            "اسم الملف",
            "الحجم",
            "تاريخ الرفع",
            "المستخدم"
        ])
        self.manuals_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.manuals_table.verticalHeader().setVisible(False)
        self.manuals_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.manuals_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.manuals_table.setAlternatingRowColors(True)

        layout.addWidget(self.manuals_table)
        self._refresh_manuals()

        self.tabs.addTab(tab, "أدلة التشغيل والمرفقات")

    def _refresh_manuals(self):
        with get_db() as db:
            atts = attachment_service.get_attachments(db, "equipment", self.equipment.id)
            self.cached_attachments = atts
            self.manuals_table.setRowCount(len(atts))
            for i, att in enumerate(atts):
                t_label = "دليل تشغيل" if att.attachment_type == "operation_manual" else (
                    "دليل صيانة" if att.attachment_type == "service_manual" else "مرفق عام"
                )
                self.manuals_table.setItem(i, 0, QTableWidgetItem(t_label))
                self.manuals_table.setItem(i, 1, QTableWidgetItem(att.file_name))
                size_kb = (att.file_size or 0) / 1024
                size_str = f"{size_kb / 1024:.1f} MB" if size_kb >= 1024 else f"{size_kb:.0f} KB"
                self.manuals_table.setItem(i, 2, QTableWidgetItem(size_str))
                d_str = att.upload_date.strftime("%Y-%m-%d") if att.upload_date else "—"
                self.manuals_table.setItem(i, 3, QTableWidgetItem(d_str))
                u_str = att.uploaded_by.full_name if att.uploaded_by else "النظام"
                self.manuals_table.setItem(i, 4, QTableWidgetItem(u_str))

    def _upload_manual(self, att_type: str):
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "اختر ملف PDF أو وثيقة فنية",
            "",
            "Documents (*.pdf *.docx *.xlsx *.png *.jpg);;All Files (*)"
        )
        if not filepath:
            return

        user = auth_service.current_user
        try:
            with get_db() as db:
                attachment_service.upload_attachment(
                    db=db,
                    user=user,
                    entity_type="equipment",
                    entity_id=self.equipment.id,
                    source_file_path=filepath,
                    attachment_type=att_type,
                    description=f"{att_type} for {self.equipment.asset_number}"
                )
            QMessageBox.information(self, "نجاح", "تم رفع الملف بنجاح وربطه بالجهاز.")
            self._refresh_manuals()
        except Exception as e:
            QMessageBox.critical(self, "خطأ في الرفع", str(e))

    def _get_selected_manual(self) -> Optional[Attachment]:
        row = self.manuals_table.currentRow()
        if 0 <= row < len(getattr(self, "cached_attachments", [])):
            return self.cached_attachments[row]
        return None

    def _open_selected_manual(self):
        att = self._get_selected_manual()
        if not att:
            QMessageBox.information(self, "تنبيه", "يرجى اختيار ملف من القائمة.")
            return

        path = att.stored_file_path
        if not os.path.exists(path):
            QMessageBox.warning(self, "ملف مفقود", "الملف غير موجود على القرص أو تم نقله.")
            return

        try:
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        except Exception as e:
            QMessageBox.critical(self, "خطأ في فتح الملف", str(e))

    def _download_selected_manual(self):
        att = self._get_selected_manual()
        if not att:
            QMessageBox.information(self, "تنبيه", "يرجى اختيار ملف من القائمة.")
            return

        dest, _ = QFileDialog.getSaveFileName(self, "حفظ نسخة من الملف", att.file_name)
        if not dest:
            return

        try:
            attachment_service.export_attachment_copy(att, dest)
            QMessageBox.information(self, "نجاح", "تم تنزيل نسخة من الملف بنجاح.")
        except Exception as e:
            QMessageBox.critical(self, "خطأ في التنزيل", str(e))

    def _delete_selected_manual(self):
        att = self._get_selected_manual()
        if not att:
            QMessageBox.information(self, "تنبيه", "يرجى اختيار ملف من القائمة.")
            return

        ans = QMessageBox.question(
            self,
            "تأكيد الحذف",
            f"هل أنت متأكد من حذف الملف '{att.file_name}'؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if ans == QMessageBox.StandardButton.Yes:
            user = auth_service.current_user
            try:
                with get_db() as db:
                    attachment_service.delete_attachment(db, user, att.id)
                self._refresh_manuals()
            except Exception as e:
                QMessageBox.critical(self, "خطأ", str(e))

    # ── Tab 4: Accessories & Costs ───────────────────────────────────────────
    def _build_tab_accessories(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # Summary Bar
        self.acc_summary_frame = QFrame()
        self.acc_summary_frame.setStyleSheet("""
            QFrame {
                background-color: #F1F5F9;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 10px 14px;
            }
        """)
        s_layout = QHBoxLayout(self.acc_summary_frame)
        s_layout.setContentsMargins(0, 0, 0, 0)

        self.acc_orig_cost_lbl = QLabel()
        self.acc_total_cost_lbl = QLabel()
        self.acc_grand_total_lbl = QLabel()

        for lbl in (self.acc_orig_cost_lbl, self.acc_total_cost_lbl, self.acc_grand_total_lbl):
            lbl.setStyleSheet("font-size: 13px; font-weight: 700; color: #0F172A;")

        s_layout.addWidget(self.acc_orig_cost_lbl)
        s_layout.addStretch()
        s_layout.addWidget(self.acc_total_cost_lbl)
        s_layout.addStretch()
        s_layout.addWidget(self.acc_grand_total_lbl)
        layout.addWidget(self.acc_summary_frame)

        # Toolbar
        bar = QHBoxLayout()
        add_btn = QPushButton("+ إضافة ملحق جديد")
        add_btn.setObjectName("primaryBtn")
        add_btn.setIcon(icon("add", color="#FFFFFF", size=14))
        add_btn.clicked.connect(self._add_accessory)
        bar.addWidget(add_btn)

        edit_btn = QPushButton("تعديل الملحق")
        edit_btn.setIcon(icon("edit", color="#0F766E", size=14))
        edit_btn.clicked.connect(self._edit_accessory)
        bar.addWidget(edit_btn)

        del_btn = QPushButton("حذف الملحق")
        del_btn.setIcon(icon("delete", color="#DC2626", size=14))
        del_btn.clicked.connect(self._delete_accessory)
        bar.addWidget(del_btn)
        bar.addStretch()
        layout.addLayout(bar)

        self.accessories_table = QTableWidget()
        self.accessories_table.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.accessories_table.setColumnCount(8)
        self.accessories_table.setHorizontalHeaderLabels([
            "اسم الملحق",
            "الموديل",
            "الرقم التسلسلي",
            "الشركة المصنعة",
            "الكمية",
            "تكلفة الوحدة",
            "إجمالي التكلفة",
            "تاريخ الإضافة"
        ])
        self.accessories_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.accessories_table.verticalHeader().setVisible(False)
        self.accessories_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.accessories_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.accessories_table.setAlternatingRowColors(True)

        layout.addWidget(self.accessories_table)
        self._refresh_accessories()

        self.tabs.addTab(tab, "ملحقات الجهاز والتكاليف")

    def _refresh_accessories(self):
        with get_db() as db:
            accs = equipment_service.get_accessories(db, self.equipment.id)
            self.cached_accessories = accs
            self.accessories_table.setRowCount(len(accs))
            total_acc_cost = 0.0

            for i, acc in enumerate(accs):
                self.accessories_table.setItem(i, 0, QTableWidgetItem(acc.name))
                self.accessories_table.setItem(i, 1, QTableWidgetItem(acc.model_number or "—"))
                self.accessories_table.setItem(i, 2, QTableWidgetItem(acc.serial_number or "—"))
                self.accessories_table.setItem(i, 3, QTableWidgetItem(acc.manufacturer or "—"))
                self.accessories_table.setItem(i, 4, QTableWidgetItem(f"{acc.quantity:g}"))
                self.accessories_table.setItem(i, 5, QTableWidgetItem(f"{acc.unit_cost:,.2f} ر.س"))
                self.accessories_table.setItem(i, 6, QTableWidgetItem(f"{acc.total_cost:,.2f} ر.س"))
                d_str = acc.added_date.strftime("%Y-%m-%d") if acc.added_date else "—"
                self.accessories_table.setItem(i, 7, QTableWidgetItem(d_str))
                total_acc_cost += float(acc.total_cost or 0.0)

            orig_price = float(self.equipment.purchase_price or 0.0)
            grand_total = orig_price + total_acc_cost

            self.acc_orig_cost_lbl.setText(f"قيمة شراء الجهاز: {orig_price:,.2f} ر.س")
            self.acc_total_cost_lbl.setText(f"إجمالي الملحقات: {total_acc_cost:,.2f} ر.س")
            self.acc_grand_total_lbl.setText(f"التكلفة الكلية المجمعة: {grand_total:,.2f} ر.س")

    def _selected_accessory(self) -> Optional[EquipmentAccessory]:
        row = self.accessories_table.currentRow()
        if 0 <= row < len(getattr(self, "cached_accessories", [])):
            return self.cached_accessories[row]
        return None

    def _add_accessory(self):
        dlg = EquipmentAccessoryDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            user = auth_service.current_user
            try:
                with get_db() as db:
                    equipment_service.add_accessory(db, user, self.equipment.id, data)
                self._refresh_accessories()
            except Exception as e:
                QMessageBox.critical(self, "خطأ", str(e))

    def _edit_accessory(self):
        acc = self._selected_accessory()
        if not acc:
            QMessageBox.information(self, "تنبيه", "يرجى اختيار ملحق من الجدول للتعديل.")
            return

        dlg = EquipmentAccessoryDialog(accessory=acc, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            user = auth_service.current_user
            try:
                with get_db() as db:
                    equipment_service.update_accessory(db, user, acc.id, data)
                self._refresh_accessories()
            except Exception as e:
                QMessageBox.critical(self, "خطأ", str(e))

    def _delete_accessory(self):
        acc = self._selected_accessory()
        if not acc:
            QMessageBox.information(self, "تنبيه", "يرجى اختيار ملحق للحذف.")
            return

        ans = QMessageBox.question(
            self,
            "تأكيد الحذف",
            f"هل أنت متأكد من حذف الملحق '{acc.name}'؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if ans == QMessageBox.StandardButton.Yes:
            user = auth_service.current_user
            try:
                with get_db() as db:
                    equipment_service.delete_accessory(db, user, acc.id)
                self._refresh_accessories()
            except Exception as e:
                QMessageBox.critical(self, "خطأ", str(e))

    # ── Tab 5: Receiving & Commissioning ─────────────────────────────────────
    def _build_tab_receiving(self):
        tab = QWidget()
        self.rec_layout = QVBoxLayout(tab)
        self.rec_layout.setContentsMargins(18, 18, 18, 18)
        self.rec_layout.setSpacing(14)

        # Toolbar
        bar = QHBoxLayout()
        edit_btn = QPushButton("تعديل بيانات الاستلام والتعميد")
        edit_btn.setObjectName("primaryBtn")
        edit_btn.setIcon(icon("edit", color="#FFFFFF", size=14))
        edit_btn.clicked.connect(self._edit_receiving)
        bar.addWidget(edit_btn)

        print_btn = QPushButton("طباعة محضر الاستلام")
        print_btn.setIcon(icon("print", color="#0F766E", size=14))
        print_btn.clicked.connect(self._print_receiving)
        bar.addWidget(print_btn)

        bar.addStretch()
        self.rec_layout.addLayout(bar)

        self.rec_grid_widget = QWidget()
        self.rec_grid = QGridLayout(self.rec_grid_widget)
        self.rec_grid.setContentsMargins(0, 8, 0, 0)
        self.rec_grid.setHorizontalSpacing(24)
        self.rec_grid.setVerticalSpacing(12)
        self.rec_layout.addWidget(self.rec_grid_widget)
        self.rec_layout.addStretch()

        self._refresh_receiving()
        self.tabs.addTab(tab, "الاستلام والتعميد")

    def _refresh_receiving(self):
        # Clear grid
        while self.rec_grid.count():
            item = self.rec_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        with get_db() as db:
            rec = equipment_service.get_receiving_data(db, self.equipment.id)
            self.cached_receiving = rec

            self._add_detail_row(self.rec_grid, 0, "رقم التعميد:", rec.commissioning_number if rec and rec.commissioning_number else "—")
            self._add_detail_row(self.rec_grid, 1, "تاريخ التعميد:", str(rec.commissioning_date if rec and rec.commissioning_date else "—"))
            self._add_detail_row(self.rec_grid, 2, "تاريخ استلام الجهاز:", str(rec.receipt_date if rec and rec.receipt_date else "—"))

            tech_str = (rec.receiving_technician_name or (rec.receiving_technician.full_name if rec.receiving_technician else "—")) if rec else "—"
            self._add_detail_row(self.rec_grid, 3, "فني الاستلام المسؤول:", tech_str)

            officer_str = (rec.registration_officer_name or (rec.registration_officer.full_name if rec.registration_officer else "—")) if rec else "—"
            self._add_detail_row(self.rec_grid, 4, "مسؤول تسجيل الجهاز:", officer_str)

            self._add_detail_row(self.rec_grid, 5, "تاريخ التسجيل:", str(rec.registration_date if rec and rec.registration_date else "—"))
            self._add_detail_row(self.rec_grid, 6, "رقم محضر الاستلام:", rec.receipt_report_number if rec and rec.receipt_report_number else "—")
            self._add_detail_row(self.rec_grid, 7, "ملاحظات الاستلام:", rec.receipt_notes if rec and rec.receipt_notes else "—")

    def _edit_receiving(self):
        dlg = EquipmentReceivingDialog(receiving=self.cached_receiving, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            user = auth_service.current_user
            try:
                with get_db() as db:
                    equipment_service.set_receiving_data(db, user, self.equipment.id, data)
                self._refresh_receiving()
            except Exception as e:
                QMessageBox.critical(self, "خطأ", str(e))

    def _print_receiving(self):
        rec = self.cached_receiving
        eq = self.equipment
        report_data = {
            "title": "محضر استلام وتعميد جهاز طبي",
            "equipment": {
                "name_ar": eq.name_ar or "—",
                "asset_number": eq.asset_number or "—",
                "model": eq.model or "—",
                "serial_number": eq.serial_number or "—",
                "department": eq.department.name_ar if eq.department else "—",
                "manufacturer": eq.manufacturer.name if eq.manufacturer else "—",
            },
            "receiving": {
                "commissioning_number": rec.commissioning_number if rec and rec.commissioning_number else "—",
                "commissioning_date": str(rec.commissioning_date) if rec and rec.commissioning_date else "—",
                "receipt_date": str(rec.receipt_date) if rec and rec.receipt_date else "—",
                "receipt_report_number": rec.receipt_report_number if rec and rec.receipt_report_number else "—",
                "receiving_technician_name": (
                    rec.receiving_technician_name or
                    (rec.receiving_technician.full_name if rec.receiving_technician else "—")
                ) if rec else "—",
                "registration_officer_name": (
                    rec.registration_officer_name or
                    (rec.registration_officer.full_name if rec.registration_officer else "—")
                ) if rec else "—",
                "registration_date": str(rec.registration_date) if rec and rec.registration_date else "—",
                "receipt_notes": rec.receipt_notes if rec and rec.receipt_notes else "—",
            },
        }
        html = report_service.generate_receiving_report_html(report_data)
        dest, _ = QFileDialog.getSaveFileName(
            self, "حفظ محضر الاستلام كملف HTML / PDF",
            f"محضر_استلام_{eq.asset_number}.html"
        )
        if dest:
            with open(dest, "w", encoding="utf-8") as f:
                f.write(html)
            QMessageBox.information(self, "نجاح", "تم حفظ محضر الاستلام بالتنسيق العربي الموحد، وهو جاهز للطباعة.")
            QDesktopServices.openUrl(QUrl.fromLocalFile(dest))

    # ── Tab 6: Work Orders ───────────────────────────────────────────────────
    def _build_tab_work_orders(self):
        eq = self.equipment
        tab_wo = QWidget()
        wo_layout = QVBoxLayout(tab_wo)
        wo_layout.setContentsMargins(14, 14, 14, 14)
        wo_table = QTableWidget()
        wo_table.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        wo_table.setColumnCount(6)
        wo_table.setHorizontalHeaderLabels([
            "رقم أمر العمل",
            "تاريخ البلاغ",
            "الأولوية",
            "الحالة",
            "الفني المسؤول",
            "وصف العطل"
        ])
        wo_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        wo_table.verticalHeader().setVisible(False)
        wo_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        wo_table.setAlternatingRowColors(True)

        wo_widths = [110, 100, 90, 100, 140, 200]
        for c, w in enumerate(wo_widths):
            wo_table.setColumnWidth(c, w)

        with get_db() as db:
            work_orders = db.query(WorkOrder).filter_by(equipment_id=eq.id).order_by(WorkOrder.created_at.desc()).all()
            wo_table.setRowCount(len(work_orders))
            for i, wo in enumerate(work_orders):
                wo_table.setItem(i, 0, QTableWidgetItem(wo.work_order_number))
                wo_table.setItem(i, 1, QTableWidgetItem(str(wo.report_date.strftime("%Y-%m-%d") if wo.report_date else "—")))
                wo_table.setItem(i, 2, QTableWidgetItem(tr(f"priority.{wo.priority}")))
                wo_table.setItem(i, 3, QTableWidgetItem(tr(f"status.{wo.status}")))
                tech_name = wo.assigned_technician.full_name if wo.assigned_technician else "غير مخصص"
                wo_table.setItem(i, 4, QTableWidgetItem(tech_name))
                wo_table.setItem(i, 5, QTableWidgetItem(wo.failure_description or "—"))
        wo_layout.addWidget(wo_table)
        self.tabs.addTab(tab_wo, "أوامر الصيانة")

    # ── Tab 7: PM ────────────────────────────────────────────────────────────
    def _build_tab_pm(self):
        eq = self.equipment
        tab_pm = QWidget()
        pm_layout = QVBoxLayout(tab_pm)
        pm_layout.setContentsMargins(14, 14, 14, 14)
        pm_table = QTableWidget()
        pm_table.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        pm_table.setColumnCount(4)
        pm_table.setHorizontalHeaderLabels([
            "تاريخ الاستحقاق",
            "خطة الصيانة",
            "الحالة",
            "نتيجة الفحص"
        ])
        pm_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        pm_table.verticalHeader().setVisible(False)
        pm_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        pm_table.setAlternatingRowColors(True)

        pm_widths = [110, 220, 100, 110]
        for c, w in enumerate(pm_widths):
            pm_table.setColumnWidth(c, w)

        with get_db() as db:
            pm_schedules = db.query(PMSchedule).filter_by(equipment_id=eq.id).order_by(PMSchedule.due_date.desc()).all()
            pm_table.setRowCount(len(pm_schedules))
            for i, sch in enumerate(pm_schedules):
                pm_table.setItem(i, 0, QTableWidgetItem(str(sch.due_date)))
                plan_title = sch.plan.title if sch.plan else "خطة دورية"
                pm_table.setItem(i, 1, QTableWidgetItem(plan_title))
                pm_table.setItem(i, 2, QTableWidgetItem(tr(f"status.{sch.status}")))
                res = "ناجح" if (sch.execution and sch.execution.passed) else ("راسب" if sch.execution else "لم ينفذ بعد")
                pm_table.setItem(i, 3, QTableWidgetItem(res))
        pm_layout.addWidget(pm_table)
        self.tabs.addTab(tab_pm, "الصيانة الوقائية")

    # ── Tab 8: Consumed Parts ────────────────────────────────────────────────
    def _build_tab_parts(self):
        eq = self.equipment
        tab_parts = QWidget()
        p_layout = QVBoxLayout(tab_parts)
        p_layout.setContentsMargins(14, 14, 14, 14)
        parts_table = QTableWidget()
        parts_table.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        parts_table.setColumnCount(5)
        parts_table.setHorizontalHeaderLabels([
            "أمر العمل",
            "اسم قطعة الغيار",
            "الكمية",
            "سعر الوحدة",
            "الإجمالي"
        ])
        parts_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        parts_table.verticalHeader().setVisible(False)
        parts_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        parts_table.setAlternatingRowColors(True)

        parts_widths = [110, 200, 80, 100, 110]
        for c, w in enumerate(parts_widths):
            parts_table.setColumnWidth(c, w)

        with get_db() as db:
            parts_used = (
                db.query(WorkOrderPart)
                .join(WorkOrder)
                .filter(WorkOrder.equipment_id == eq.id)
                .all()
            )
            parts_table.setRowCount(len(parts_used))
            for i, wp in enumerate(parts_used):
                wo_num = wp.work_order.work_order_number if wp.work_order else "—"
                part_name = wp.part.name_ar if (wp.part and wp.part.name_ar) else (wp.part.name_en if wp.part else "—")
                parts_table.setItem(i, 0, QTableWidgetItem(wo_num))
                parts_table.setItem(i, 1, QTableWidgetItem(part_name))
                parts_table.setItem(i, 2, QTableWidgetItem(f"{wp.quantity:g}"))
                parts_table.setItem(i, 3, QTableWidgetItem(f"{wp.unit_price:,.2f} ر.س"))
                parts_table.setItem(i, 4, QTableWidgetItem(f"{wp.total_price:,.2f} ر.س"))
        p_layout.addWidget(parts_table)
        self.tabs.addTab(tab_parts, "قطع الغيار المستهلكة")

    # ── Tab 9: Transfers ─────────────────────────────────────────────────────
    def _build_tab_transfers(self):
        eq = self.equipment
        tab_transfers = QWidget()
        t_layout = QVBoxLayout(tab_transfers)
        t_layout.setContentsMargins(14, 14, 14, 14)

        transfer_table = QTableWidget()
        transfer_table.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        transfer_table.setColumnCount(4)
        transfer_table.setHorizontalHeaderLabels([
            "تاريخ النقل",
            "من قسم",
            "إلى قسم",
            "سبب النقل"
        ])
        transfer_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        transfer_table.verticalHeader().setVisible(False)
        transfer_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        transfer_table.setAlternatingRowColors(True)

        transfer_widths = [110, 160, 160, 180]
        for c, w in enumerate(transfer_widths):
            transfer_table.setColumnWidth(c, w)

        with get_db() as db:
            transfers = db.query(EquipmentTransfer).filter_by(equipment_id=eq.id).order_by(EquipmentTransfer.transfer_date.desc()).all()
            transfer_table.setRowCount(len(transfers))
            for i, tr_rec in enumerate(transfers):
                transfer_table.setItem(i, 0, QTableWidgetItem(str(tr_rec.transfer_date)))
                f_name = tr_rec.from_department.name_ar if tr_rec.from_department else "—"
                transfer_table.setItem(i, 1, QTableWidgetItem(f_name))
                t_name = tr_rec.to_department.name_ar if tr_rec.to_department else "—"
                transfer_table.setItem(i, 2, QTableWidgetItem(t_name))
                transfer_table.setItem(i, 3, QTableWidgetItem(tr_rec.reason or "—"))

        t_layout.addWidget(transfer_table)
        self.tabs.addTab(tab_transfers, "سجل النقل")

    def _on_edit(self):
        self.accept()
        self.edit_requested.emit(self.equipment.id)

    def _on_transfer(self):
        self.accept()
        self.transfer_requested.emit(self.equipment.id)

    def _on_export_report(self):
        try:
            with get_db() as db:
                data = report_service.get_equipment_history_report_data(db, self.equipment.id)
            if not data:
                QMessageBox.warning(self, "تنبيه", "تعذر جلب بيانات تقرير صيانة الجهاز.")
                return

            html = report_service.generate_equipment_history_html(data)

            printer = QPrinter(QPrinter.PrinterMode.ScreenResolution)
            orientation = report_service.get_page_orientation(data)
            printer.setPageOrientation(
                QPageLayout.Orientation.Landscape if orientation == "landscape"
                else QPageLayout.Orientation.Portrait
            )
            printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
            printer.setPageMargins(QMarginsF(8, 8, 8, 8), QPageLayout.Unit.Millimeter)

            def _paint_preview(target_printer):
                doc = QTextDocument()
                paint_rect = target_printer.pageLayout().paintRectPixels(target_printer.resolution())
                doc.setPageSize(QSizeF(paint_rect.width(), paint_rect.height()))
                report_service.prepare_rtl_document(doc, html, font_size=9)
                doc.print_(target_printer)

            preview = QPrintPreviewDialog(printer, self)
            preview.setWindowTitle(f"تقرير صيانة الجهاز الطبي — {self.equipment.asset_number}")
            preview.resize(1050, 800)
            preview.paintRequested.connect(_paint_preview)
            preview.exec()
        except Exception as e:
            QMessageBox.critical(self, "خطأ في الطباعة", f"فشل فتح تقرير الصيانة: {str(e)}")

