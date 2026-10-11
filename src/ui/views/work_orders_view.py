"""
Work Orders View for Corrective Maintenance tracking.
Pure Arabic, RTL, zero emojis, enterprise layout, status & priority badges.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox,
    QPushButton, QLabel, QTableWidgetItem, QMessageBox, QFrame, QHeaderView
)
from PySide6.QtCore import Qt, QSizeF, QMarginsF
from PySide6.QtGui import QTextDocument, QPageSize, QPageLayout, QFont
from PySide6.QtPrintSupport import QPrinter, QPrintPreviewDialog
from src.core.i18n import tr
from src.core.database import get_db
from src.services.work_order_service import work_order_service
from src.services.report_service import report_service
from src.ui.theme.icons import icon
from src.ui.components.status_badge import StatusBadge
from src.ui.components.data_table import DataTable
from src.ui.components.action_button import ActionButton, create_actions_cell
from src.ui.views.work_order_dialog import WorkOrderDialog


class WorkOrdersView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 14, 18, 14)
        main_layout.setSpacing(10)

        # Header Frame
        header_frame = QFrame()
        h_layout = QHBoxLayout(header_frame)
        h_layout.setContentsMargins(0, 0, 0, 0)

        titles_box = QVBoxLayout()
        titles_box.setSpacing(2)
        self.title_lbl = QLabel("أوامر الصيانة الطارئة والبلاغات (Work Orders)")
        self.title_lbl.setStyleSheet("font-size: 16px; font-weight: 800; color: #0F172A;")

        self.subtitle_lbl = QLabel("متابعة بلاغات الأعطال، تكليف الفنيين، وتوثيق الإصلاحات وقطع الغيار المستهلكة")
        self.subtitle_lbl.setStyleSheet("font-size: 11px; color: #64748B; font-weight: 500;")

        titles_box.addWidget(self.title_lbl)
        titles_box.addWidget(self.subtitle_lbl)
        h_layout.addLayout(titles_box)
        h_layout.addStretch()

        main_layout.addWidget(header_frame)

        # Filter Card
        filter_card = QFrame()
        filter_card.setStyleSheet("""
            QFrame {
                background-color: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                padding: 8px 12px;
            }
        """)
        filter_layout = QHBoxLayout(filter_card)
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.setSpacing(10)

        self.filter_lbl = QLabel("تصفية حسب:")
        self.filter_lbl.setStyleSheet("font-weight: 700; color: #475569; font-size: 11px;")
        filter_layout.addWidget(self.filter_lbl)

        filter_layout.addWidget(QLabel("الحالة:"))
        self.status_filter = QComboBox()
        self.status_filter.currentIndexChanged.connect(self.load_data)
        filter_layout.addWidget(self.status_filter)

        filter_layout.addWidget(QLabel("الأولوية:"))
        self.priority_filter = QComboBox()
        self.priority_filter.currentIndexChanged.connect(self.load_data)
        filter_layout.addWidget(self.priority_filter)

        filter_layout.addStretch()

        self.reset_btn = QPushButton("إلغاء الفلتر")
        self.reset_btn.setProperty("variant", "secondary")
        self.reset_btn.setIcon(icon("clear", color="#64748B", size=12))
        self.reset_btn.clicked.connect(self._reset_filters)
        filter_layout.addWidget(self.reset_btn)

        main_layout.addWidget(filter_card)

        # Data Table
        headers = [
            "رقم أمر العمل",
            "الجهاز الطبي",
            "القسم",
            "وصف العطل / البلاغ",
            "الأولوية",
            "الحالة",
            "الفني المسؤول",
            "مقدم البلاغ",
            "تاريخ البلاغ",
            "الإجراءات"
        ]

        self.table_widget = DataTable()
        self.table_widget.set_search_placeholder("بحث برقم أمر العمل، اسم الجهاز، أو مقدم البلاغ...")
        self.table_widget.set_headers(headers)
        self.table_widget.set_add_button_text("+ فتح أمر صيانة")
        self.table_widget.search_changed.connect(lambda txt: self.load_data())
        self.table_widget.refresh_requested.connect(self.load_data)
        self.table_widget.add_clicked.connect(self._on_add)
        # 0: WO#, 1: Equip, 2: Dept, 3: Desc, 4: Priority, 5: Status, 6: Tech, 7: Reporter, 8: Date, 9: Actions
        self.table_widget.set_column_widths([110, 190, 150, 180, 95, 100, 120, 110, 95, 80], stretch_cols=[1, 2, 3])
        self.table_widget.table.verticalHeader().setDefaultSectionSize(38)

        main_layout.addWidget(self.table_widget, stretch=1)

        self._populate_filters()
        self.load_data()

    def _populate_filters(self):
        self.status_filter.clear()
        self.status_filter.addItem("جميع الحالات", None)
        for s in ["pending", "assigned", "in_progress", "waiting_parts", "completed", "closed", "cancelled"]:
            self.status_filter.addItem(tr(f"status.{s}"), s)

        self.priority_filter.clear()
        self.priority_filter.addItem("جميع الأولويات", None)
        for p in ["critical", "high", "medium", "low"]:
            self.priority_filter.addItem(tr(f"priority.{p}"), p)

    def _reset_filters(self):
        self.status_filter.setCurrentIndex(0)
        self.priority_filter.setCurrentIndex(0)
        self.table_widget.search_input.clear()
        self.load_data()

    def load_data(self):
        search_txt = self.table_widget.search_input.text().strip()
        status = self.status_filter.currentData()
        priority = self.priority_filter.currentData()

        with get_db() as db:
            orders = work_order_service.get_work_orders(
                db=db,
                search_query=search_txt or None,
                status=status,
                priority=priority
            )

            tbl = self.table_widget.table
            tbl.setRowCount(len(orders))

            for row_idx, wo in enumerate(orders):
                it_num = QTableWidgetItem(wo.work_order_number)
                it_num.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                tbl.setItem(row_idx, 0, it_num)

                eq_name = wo.equipment.name_ar or wo.equipment.name_en if wo.equipment else "—"
                eq_asset = wo.equipment.asset_number if wo.equipment else "—"
                it_eq = QTableWidgetItem(f"{eq_asset} — {eq_name}")
                it_eq.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                tbl.setItem(row_idx, 1, it_eq)
                
                dept_name = wo.department.name_ar if wo.department else (wo.equipment.department.name_ar if wo.equipment and wo.equipment.department else "—")
                it_dept = QTableWidgetItem(dept_name)
                it_dept.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                tbl.setItem(row_idx, 2, it_dept)

                desc = (wo.failure_description[:40] + "...") if len(wo.failure_description or "") > 40 else (wo.failure_description or "—")
                it_desc = QTableWidgetItem(desc)
                it_desc.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                tbl.setItem(row_idx, 3, it_desc)

                # Priority Badge
                tbl.setCellWidget(row_idx, 4, StatusBadge(wo.priority))

                # Status Badge
                tbl.setCellWidget(row_idx, 5, StatusBadge(wo.status))

                tech_name = wo.assigned_technician.full_name if wo.assigned_technician else "غير مخصص"
                it_tech = QTableWidgetItem(tech_name)
                it_tech.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                tbl.setItem(row_idx, 6, it_tech)

                it_rep = QTableWidgetItem(wo.reported_by_name or "—")
                it_rep.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                tbl.setItem(row_idx, 7, it_rep)

                it_date = QTableWidgetItem(wo.created_at.strftime("%Y-%m-%d") if wo.created_at else "—")
                it_date.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                tbl.setItem(row_idx, 8, it_date)

                # Actions (Edit, Print Ticket)
                edit_btn = ActionButton(
                    action_type="edit",
                    tooltip="تعديل وتحديث أمر الصيانة",
                    callback=lambda _, w_id=wo.id: self._on_edit(w_id)
                )
                print_btn = ActionButton(
                    action_type="print",
                    tooltip="طباعة وتصدير تذكرة أمر الصيانة",
                    callback=lambda _, w_id=wo.id: self._on_print_ticket(w_id)
                )

                actions_widget = create_actions_cell(edit_btn, print_btn)
                tbl.setCellWidget(row_idx, 9, actions_widget)

            self.table_widget.set_record_count(len(orders), len(orders))

    def _on_add(self):
        dlg = WorkOrderDialog(parent=self)
        if dlg.exec() == WorkOrderDialog.DialogCode.Accepted:
            self.load_data()

    def _on_edit(self, wo_id: int):
        with get_db() as db:
            wo = work_order_service.get_work_order_by_id(db, wo_id)
            if not wo:
                return
            dlg = WorkOrderDialog(work_order=wo, parent=self)
            if dlg.exec() == WorkOrderDialog.DialogCode.Accepted:
                self.load_data()

    def _on_print_ticket(self, wo_id: int):
        try:
            with get_db() as db:
                data = report_service.get_work_order_ticket_data(db, wo_id)
            if not data:
                QMessageBox.warning(self, "تنبيه", "تعذر جلب بيانات أمر الصيانة.")
                return

            html = report_service.generate_work_order_ticket_html(data)

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
            wo_num = data.get("work_order", {}).get("number", str(wo_id))
            preview.setWindowTitle(f"تذكرة أمر صيانة رقم {wo_num} — هيئة مستشفى الثورة")
            preview.resize(1000, 780)
            preview.paintRequested.connect(_paint_preview)
            preview.exec()
        except Exception as e:
            QMessageBox.critical(self, "خطأ في الطباعة", f"فشل فتح تذكرة أمر الصيانة: {str(e)}")

    def retranslate_ui(self):
        self.load_data()
