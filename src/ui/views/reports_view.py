"""
Enterprise Reports & Analytics View.
Pure Arabic, RTL, zero emojis, real-time KPI aggregations, print preview, and multi-format exports (Excel, PDF, CSV).
"""
import os
from datetime import datetime, date, timedelta
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QDateEdit, QFileDialog, QMessageBox,
    QTableWidgetItem, QHeaderView, QFrame
)
from PySide6.QtCore import Qt, QDate, QTimer, QSizeF, QMarginsF
from PySide6.QtGui import QTextDocument, QPageSize, QPageLayout, QPdfWriter, QFont
from PySide6.QtPrintSupport import QPrinter, QPrintPreviewDialog, QPrintDialog

from src.core.i18n import tr
from src.core.database import get_db
from src.services.report_service import report_service
from src.models.hospital import Department
from src.models.vendor import Vendor
from src.models.equipment import Equipment
from src.ui.theme.icons import icon
from src.ui.components.stat_card import StatCard
from src.ui.components.data_table import DataTable


class ReportsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_report_data = {}
        self.all_departments = []
        self.all_manufacturers = []
        self.all_vendors = []
        self._setup_ui()
        QTimer.singleShot(0, self.refresh_data)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 14, 18, 14)
        main_layout.setSpacing(10)

        # ── 1. Header Section ────────────────────────────────────────────────
        header_layout = QHBoxLayout()
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)

        self.title_lbl = QLabel("التقارير المتقدمة والتحليلات")
        self.title_lbl.setStyleSheet("font-size: 18px; font-weight: 800; color: #0F172A;")
        self.sub_lbl = QLabel("استخراج وتصدير تقارير الأصول، بلاغات الصيانة، الامتثال للوقائية، والمخزون والشركات")
        self.sub_lbl.setStyleSheet("font-size: 12px; color: #64748B;")
        title_layout.addWidget(self.title_lbl)
        title_layout.addWidget(self.sub_lbl)
        header_layout.addLayout(title_layout)
        header_layout.addStretch()

        # Print / Preview Button
        self.print_btn = QPushButton("معاينة وطباعة")
        self.print_btn.setIcon(icon("reports", color="#FFFFFF", size=15))
        self.print_btn.setStyleSheet("""
            QPushButton {
                background-color: #0284C7;
                color: #FFFFFF;
                font-weight: 700;
                font-size: 12px;
                padding: 7px 14px;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #0369A1; }
        """)
        self.print_btn.clicked.connect(self._print_report)

        # Export Buttons
        self.export_excel_btn = QPushButton("تصدير Excel")
        self.export_excel_btn.setIcon(icon("export_excel", color="#FFFFFF", size=15))
        self.export_excel_btn.setStyleSheet("""
            QPushButton {
                background-color: #059669;
                color: #FFFFFF;
                font-weight: 700;
                font-size: 12px;
                padding: 7px 14px;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #047857; }
        """)
        self.export_excel_btn.clicked.connect(self._export_excel)

        self.export_pdf_btn = QPushButton("تصدير PDF (عربي)")
        self.export_pdf_btn.setIcon(icon("export_pdf", color="#FFFFFF", size=15))
        self.export_pdf_btn.setStyleSheet("""
            QPushButton {
                background-color: #DC2626;
                color: #FFFFFF;
                font-weight: 700;
                font-size: 12px;
                padding: 7px 14px;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #B91C1C; }
        """)
        self.export_pdf_btn.clicked.connect(self._export_pdf)

        self.export_csv_btn = QPushButton("تصدير CSV")
        self.export_csv_btn.setIcon(icon("reports", color="#475569", size=15))
        self.export_csv_btn.setStyleSheet("""
            QPushButton {
                background-color: #E2E8F0;
                color: #334155;
                font-weight: 700;
                font-size: 12px;
                padding: 7px 14px;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #CBD5E1; }
        """)
        self.export_csv_btn.clicked.connect(self._export_csv)

        header_layout.addWidget(self.print_btn)
        header_layout.addWidget(self.export_excel_btn)
        header_layout.addWidget(self.export_pdf_btn)
        header_layout.addWidget(self.export_csv_btn)
        main_layout.addLayout(header_layout)

        # ── 2. Report Selector & Filter Bar ──────────────────────────────────
        filter_card = QFrame()
        filter_card.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        filter_layout = QHBoxLayout(filter_card)
        filter_layout.setContentsMargins(10, 8, 10, 8)
        filter_layout.setSpacing(10)

        # Report Type Selector
        type_layout = QVBoxLayout()
        type_layout.setSpacing(2)
        self.report_type_lbl = QLabel("نوع التقرير:")
        self.report_type_lbl.setStyleSheet("font-size: 11px; font-weight: bold; color: #475569;")
        self.report_type_combo = QComboBox()
        self.report_type_combo.setMinimumWidth(210)
        self.report_type_combo.addItem("تقرير سجل وحصر الأجهزة الطبية", "equipment")
        self.report_type_combo.addItem("تقرير أوامر الصيانة الطارئة والبلاغات", "work_orders")
        self.report_type_combo.addItem("تقرير مؤشر الامتثال للصيانة الوقائية", "pm_compliance")
        self.report_type_combo.addItem("تقرير تقييم وحركة قطع الغيار والمخزون", "inventory")
        self.report_type_combo.addItem("تقرير الأجهزة حسب الشركة المصنعة", "manufacturer")
        self.report_type_combo.addItem("تقرير الأجهزة حسب الوكيل والمورد", "vendor_agent")
        self.report_type_combo.addItem("تقرير الأجهزة حسب نوع الجهاز والتصنيف", "category")
        self.report_type_combo.addItem("تقرير الأجهزة الشامل حسب القسم", "department_summary")
        self.report_type_combo.addItem("تقرير متابعة عقود الضمان وانتهاء الصلاحية", "warranty")
        self.report_type_combo.addItem("تقرير ملخص أعمال الصيانة والتكاليف", "periodic_maintenance")
        self.report_type_combo.addItem("تقرير السجل الفني وتاريخ صيانة جهاز محدد", "equipment_history")
        self.report_type_combo.currentIndexChanged.connect(self._on_report_type_changed)
        type_layout.addWidget(self.report_type_lbl)
        type_layout.addWidget(self.report_type_combo)
        filter_layout.addLayout(type_layout)

        # Department Filter
        self.dept_layout = QVBoxLayout()
        self.dept_layout.setSpacing(2)
        self.dept_filter_lbl = QLabel("القسم الطبي:")
        self.dept_filter_lbl.setStyleSheet("font-size: 11px; font-weight: bold; color: #475569;")
        self.dept_combo = QComboBox()
        self.dept_combo.setMinimumWidth(150)
        self.dept_combo.addItem("جميع الأقسام", None)
        self.dept_combo.currentIndexChanged.connect(self._load_active_report)
        self.dept_layout.addWidget(self.dept_filter_lbl)
        self.dept_layout.addWidget(self.dept_combo)
        filter_layout.addLayout(self.dept_layout)

        # Dynamic Second Filter (Manufacturer / Vendor / Warranty / Category)
        self.dynamic_filter_layout = QVBoxLayout()
        self.dynamic_filter_layout.setSpacing(2)
        self.dynamic_filter_lbl = QLabel("تصفية إضافية:")
        self.dynamic_filter_lbl.setStyleSheet("font-size: 11px; font-weight: bold; color: #475569;")
        self.dynamic_combo = QComboBox()
        self.dynamic_combo.setMinimumWidth(170)
        self.dynamic_combo.currentIndexChanged.connect(self._load_active_report)
        self.dynamic_filter_layout.addWidget(self.dynamic_filter_lbl)
        self.dynamic_filter_layout.addWidget(self.dynamic_combo)
        filter_layout.addLayout(self.dynamic_filter_layout)

        # From Date Filter
        self.date_from_layout = QVBoxLayout()
        self.date_from_layout.setSpacing(2)
        self.date_from_lbl = QLabel("من تاريخ:")
        self.date_from_lbl.setStyleSheet("font-size: 11px; font-weight: bold; color: #475569;")
        self.date_from_edit = QDateEdit()
        self.date_from_edit.setCalendarPopup(True)
        self.date_from_edit.setDate(QDate.currentDate().addMonths(-1))
        self.date_from_edit.dateChanged.connect(self._load_active_report)
        self.date_from_layout.addWidget(self.date_from_lbl)
        self.date_from_layout.addWidget(self.date_from_edit)
        filter_layout.addLayout(self.date_from_layout)

        # To Date Filter
        self.date_to_layout = QVBoxLayout()
        self.date_to_layout.setSpacing(2)
        self.date_to_lbl = QLabel("إلى تاريخ:")
        self.date_to_lbl.setStyleSheet("font-size: 11px; font-weight: bold; color: #475569;")
        self.date_to_edit = QDateEdit()
        self.date_to_edit.setCalendarPopup(True)
        self.date_to_edit.setDate(QDate.currentDate())
        self.date_to_edit.dateChanged.connect(self._load_active_report)
        self.date_to_layout.addWidget(self.date_to_lbl)
        self.date_to_layout.addWidget(self.date_to_edit)
        filter_layout.addLayout(self.date_to_layout)

        # Refresh Button
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(2)
        btn_layout.addWidget(QLabel(" "))  # spacer
        self.refresh_btn = QPushButton("تحديث التقرير")
        self.refresh_btn.setIcon(icon("refresh", color="#0F766E", size=14))
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #F1F5F9;
                color: #0F766E;
                font-weight: 700;
                padding: 6px 14px;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #E2E8F0; }
        """)
        self.refresh_btn.clicked.connect(self.refresh_data)
        btn_layout.addWidget(self.refresh_btn)
        filter_layout.addLayout(btn_layout)

        filter_layout.addStretch()
        main_layout.addWidget(filter_card)

        # ── 3. KPI Stat Cards ────────────────────────────────────────────────
        self.stats_layout = QHBoxLayout()
        self.stats_layout.setSpacing(10)

        self.stat_card_1 = StatCard(title="إجمالي السجلات", value="0", icon_name="equipment", accent_color="#0284C7")
        self.stat_card_2 = StatCard(title="المكتمل / السليم", value="0", icon_name="check", accent_color="#059669")
        self.stat_card_3 = StatCard(title="تحت الصيانة / متأخر", value="0", icon_name="warning", accent_color="#D97706")
        self.stat_card_4 = StatCard(title="القيمة المالية الإجمالية", value="0 ر.س", icon_name="dashboard", accent_color="#7C3AED")
        for card in (self.stat_card_1, self.stat_card_2, self.stat_card_3, self.stat_card_4):
            card.setFixedHeight(72)

        self.stats_layout.addWidget(self.stat_card_1)
        self.stats_layout.addWidget(self.stat_card_2)
        self.stats_layout.addWidget(self.stat_card_3)
        self.stats_layout.addWidget(self.stat_card_4)
        main_layout.addLayout(self.stats_layout)

        # ── 4. Table Preview ─────────────────────────────────────────────────
        self.table_widget = DataTable()
        self.table_widget.set_add_button_visible(False)
        self.table_widget.set_search_placeholder("بحث في بيانات التقرير المعروض...")
        self.table_widget.search_changed.connect(self._on_search)
        self.table_widget.refresh_requested.connect(self._load_active_report)
        main_layout.addWidget(self.table_widget, stretch=1)

    def refresh_data(self):
        self._load_lookup_data()
        self._on_report_type_changed()

    def _load_lookup_data(self):
        try:
            with get_db() as db:
                depts = db.query(Department).order_by(Department.name_ar.asc()).all()
                self.all_departments = depts
                self.dept_combo.blockSignals(True)
                curr_dept = self.dept_combo.currentData()
                self.dept_combo.clear()
                self.dept_combo.addItem("جميع الأقسام", None)
                for d in depts:
                    name = d.name_ar if d.name_ar else d.name_en
                    self.dept_combo.addItem(name, d.id)
                idx = self.dept_combo.findData(curr_dept)
                if idx >= 0:
                    self.dept_combo.setCurrentIndex(idx)
                self.dept_combo.blockSignals(False)

                vendors = db.query(Vendor).order_by(Vendor.name.asc()).all()
                self.all_vendors = vendors
                self.all_manufacturers = [v for v in vendors if v.vendor_type in ("manufacturer", "supplier")]
        except Exception as e:
            print(f"Error loading lookup data in reports: {e}")

    def _on_report_type_changed(self):
        rtype = self.report_type_combo.currentData()
        is_date_relevant = rtype in ["work_orders", "pm_compliance", "periodic_maintenance"]
        self.date_from_edit.setEnabled(is_date_relevant)
        self.date_to_edit.setEnabled(is_date_relevant)

        # Department combo visibility/enablement
        dept_relevant = rtype in ["equipment", "work_orders", "manufacturer", "category", "department_summary", "warranty", "periodic_maintenance"]
        self.dept_combo.setEnabled(dept_relevant)

        # Configure Dynamic Second Filter
        self.dynamic_combo.blockSignals(True)
        self.dynamic_combo.clear()

        if rtype == "manufacturer":
            self.dynamic_filter_lbl.setText("الشركة المصنعة:")
            self.dynamic_filter_lbl.setVisible(True)
            self.dynamic_combo.setVisible(True)
            self.dynamic_combo.addItem("جميع الشركات المصنعة", None)
            for m in self.all_manufacturers:
                self.dynamic_combo.addItem(m.name, m.id)
        elif rtype == "vendor_agent":
            self.dynamic_filter_lbl.setText("الوكيل / المورد:")
            self.dynamic_filter_lbl.setVisible(True)
            self.dynamic_combo.setVisible(True)
            self.dynamic_combo.addItem("جميع الوكلاء والموردين", None)
            for v in self.all_vendors:
                self.dynamic_combo.addItem(v.name, v.id)
        elif rtype == "warranty":
            self.dynamic_filter_lbl.setText("حالة الضمان:")
            self.dynamic_filter_lbl.setVisible(True)
            self.dynamic_combo.setVisible(True)
            self.dynamic_combo.addItem("جميع حالات الضمان", "all")
            self.dynamic_combo.addItem("تحت الضمان الساري", "under_warranty")
            self.dynamic_combo.addItem("يوشك على الانتهاء (60 يوم)", "expiring_soon")
            self.dynamic_combo.addItem("منتهي الضمان", "expired")
        elif rtype in ("category", "equipment"):
            self.dynamic_filter_lbl.setText("تصنيف الجهاز:")
            self.dynamic_filter_lbl.setVisible(True)
            self.dynamic_combo.setVisible(True)
            self.dynamic_combo.addItem("جميع التصنيفات", "all")
            try:
                with get_db() as db:
                    db_cats = [
                        c[0] for c in db.query(Equipment.category).distinct().filter(Equipment.category.isnot(None)).all()
                    ]
                for cat in sorted(db_cats):
                    if cat:
                        self.dynamic_combo.addItem(cat, cat)
            except Exception as e:
                print(f"Error loading categories in reports: {e}")
                standard_cats = [
                    "أجهزة عناية وتنفس", "أجهزة أشعة وتصوير", "أجهزة قسطرة وعمليات",
                    "أجهزة تخدير وعمليات", "أجهزة غسيل كلى", "أجهزة مناظير جراحية",
                    "أجهزة طوارئ وإنعاش", "أجهزة مراقبة وتشخيص", "أجهزة تعقيم وتطهير",
                    "أجهزة أطفال ورعاية", "أجهزة مختبرات وتحليل", "أجهزة قلب وتشخيص",
                    "أجهزة عمليات وجراحة"
                ]
                for cat in standard_cats:
                    self.dynamic_combo.addItem(cat, cat)
        elif rtype == "inventory":
            self.dynamic_filter_lbl.setText("تصفية المخزون:")
            self.dynamic_filter_lbl.setVisible(True)
            self.dynamic_combo.setVisible(True)
            self.dynamic_combo.addItem("جميع قطع الغيار", "all")
            self.dynamic_combo.addItem("القطع قاربت على النفاد فقط", "low_stock")
        elif rtype == "equipment_history":
            self.dynamic_filter_lbl.setText("الجهاز الطبي المطلوب:")
            self.dynamic_filter_lbl.setVisible(True)
            self.dynamic_combo.setVisible(True)
            try:
                with get_db() as db:
                    eqs = db.query(Equipment).order_by(Equipment.id.asc()).all()
                for eq in eqs:
                    label = f"{eq.asset_number} — {eq.name_ar or eq.name_en}"
                    self.dynamic_combo.addItem(label, eq.id)
            except Exception as e:
                print(f"Error loading equipment list in reports: {e}")
        else:
            self.dynamic_filter_lbl.setVisible(False)
            self.dynamic_combo.setVisible(False)

        self.dynamic_combo.blockSignals(False)
        self._load_active_report()

    def _load_active_report(self):
        rtype = self.report_type_combo.currentData()
        dept_id = self.dept_combo.currentData()
        extra_val = self.dynamic_combo.currentData()
        q_from = self.date_from_edit.date()
        q_to = self.date_to_edit.date()
        from_d = date(q_from.year(), q_from.month(), q_from.day())
        to_d = date(q_to.year(), q_to.month(), q_to.day())

        with get_db() as db:
            if rtype == "equipment":
                cat = extra_val if (extra_val and extra_val != "all") else None
                data = report_service.get_equipment_report_data(db, department_id=dept_id, category=cat)
                summary = data["summary"]
                self.stat_card_1.set_title("إجمالي الأجهزة الطبية")
                self.stat_card_1.set_value(f"{summary['total_count']:,}")
                self.stat_card_2.set_title("أجهزة تعمل بكفاءة")
                self.stat_card_2.set_value(f"{summary['operational_count']:,}")
                self.stat_card_3.set_title("أجهزة تحت الصيانة")
                self.stat_card_3.set_value(f"{summary['in_maintenance']:,}")
                self.stat_card_4.set_title("القيمة التقديرية للأجهزة")
                self.stat_card_4.set_value(f"{summary['total_value']:,.0f} ر.س")

            elif rtype == "work_orders":
                data = report_service.get_work_orders_report_data(
                    db, from_date=from_d, to_date=to_d, department_id=dept_id
                )
                summary = data["summary"]
                self.stat_card_1.set_title("إجمالي بلاغات الصيانة")
                self.stat_card_1.set_value(f"{summary['total_orders']:,}")
                self.stat_card_2.set_title("أوامر مكتملة ومغلقة")
                self.stat_card_2.set_value(f"{summary['completed_count']:,}")
                self.stat_card_3.set_title("قيد التنفيذ / معلقة")
                self.stat_card_3.set_value(f"{summary['open_count'] + summary['in_progress']:,}")
                self.stat_card_4.set_title("إجمالي تكاليف الإصلاح")
                self.stat_card_4.set_value(f"{summary['total_cost']:,.0f} ر.س")

            elif rtype == "pm_compliance":
                data = report_service.get_pm_compliance_report_data(
                    db, from_date=from_d, to_date=to_d
                )
                summary = data["summary"]
                self.stat_card_1.set_title("إجمالي المواعيد المجدولة")
                self.stat_card_1.set_value(f"{summary['total_scheduled']:,}")
                self.stat_card_2.set_title("فحوصات منفذة بنجاح")
                self.stat_card_2.set_value(f"{summary['completed_count']:,}")
                self.stat_card_3.set_title("مواعيد متأخرة / معلقة")
                self.stat_card_3.set_value(f"{summary['pending_count'] + summary['overdue_count']:,}")
                self.stat_card_4.set_title("نسبة الامتثال الوقائي")
                self.stat_card_4.set_value(f"{summary['compliance_rate']}%")

            elif rtype == "inventory":
                is_low_stock = (extra_val == "low_stock")
                cat_val = None if (extra_val in (None, "all", "low_stock")) else extra_val
                data = report_service.get_inventory_report_data(db, category=cat_val, low_stock_only=is_low_stock)
                summary = data["summary"]
                self.stat_card_1.set_title("إجمالي أصناف قطع الغيار")
                self.stat_card_1.set_value(f"{summary['total_parts']:,}")
                self.stat_card_2.set_title("إجمالي كميات القطع")
                self.stat_card_2.set_value(f"{summary['total_quantity']:,}")
                self.stat_card_3.set_title("أصناف قاربت على النفاد")
                self.stat_card_3.set_value(f"{summary['low_stock_count']:,}")
                self.stat_card_4.set_title("القيمة التقديرية للمخزون")
                self.stat_card_4.set_value(f"{summary['total_valuation']:,.0f} ر.س")

            elif rtype == "manufacturer":
                manuf_id = extra_val if isinstance(extra_val, int) else None
                data = report_service.get_manufacturer_report_data(db, manufacturer_id=manuf_id, department_id=dept_id)
                summary = data["summary"]
                self.stat_card_1.set_title("إجمالي الأجهزة المصنعة")
                self.stat_card_1.set_value(f"{summary.get('total_count', 0):,}")
                self.stat_card_2.set_title("أجهزة عاملة بكفاءة")
                self.stat_card_2.set_value(f"{summary.get('operational_count', 0):,}")
                self.stat_card_3.set_title("أجهزة تحت الضمان")
                self.stat_card_3.set_value(f"{summary.get('under_warranty', 0):,}")
                self.stat_card_4.set_title("إجمالي القيمة التقديرية")
                self.stat_card_4.set_value(f"{summary.get('total_value', 0):,.0f} ر.س")

            elif rtype == "vendor_agent":
                v_id = extra_val if isinstance(extra_val, int) else None
                data = report_service.get_vendor_agent_report_data(db, vendor_id=v_id)
                summary = data["summary"]
                self.stat_card_1.set_title("إجمالي الأجهزة المسندة")
                self.stat_card_1.set_value(f"{summary.get('total_count', 0):,}")
                self.stat_card_2.set_title("أجهزة عاملة")
                self.stat_card_2.set_value(f"{summary.get('operational_count', 0):,}")
                self.stat_card_3.set_title("تحت الصيانة")
                self.stat_card_3.set_value(f"{summary.get('in_maintenance', 0):,}")
                self.stat_card_4.set_title("الوكلاء والموردون النشطون")
                self.stat_card_4.set_value(f"{len(self.all_vendors):,}")

            elif rtype == "category":
                cat = extra_val if (extra_val and extra_val != "all") else None
                data = report_service.get_category_report_data(db, category=cat, department_id=dept_id)
                summary = data["summary"]
                self.stat_card_1.set_title("إجمالي الأجهزة المشمولة")
                self.stat_card_1.set_value(f"{summary.get('total_count', 0):,}")
                self.stat_card_2.set_title("أجهزة عاملة")
                self.stat_card_2.set_value(f"{summary.get('operational_count', 0):,}")
                self.stat_card_3.set_title("أجهزة عالية الخطورة")
                self.stat_card_3.set_value(f"{summary.get('high_risk_count', 0):,}")
                self.stat_card_4.set_title("القسم المحدد")
                self.stat_card_4.set_value(self.dept_combo.currentText())

            elif rtype == "department_summary":
                data = report_service.get_department_report_data(db, department_id=dept_id)
                summary = data["summary"]
                self.stat_card_1.set_title("الأقسام المشمولة")
                self.stat_card_1.set_value(f"{summary.get('departments_count', 0):,}")
                self.stat_card_2.set_title("إجمالي الأجهزة بالمستشفى")
                self.stat_card_2.set_value(f"{summary.get('grand_total', 0):,}")
                self.stat_card_3.set_title("إجمالي الأجهزة المتوقفة")
                self.stat_card_3.set_value(f"{summary.get('grand_down', 0):,}")
                self.stat_card_4.set_title("أوامر العمل المفتوحة")
                self.stat_card_4.set_value(f"{summary.get('grand_open_wo', 0):,}")

            elif rtype == "warranty":
                w_filter = extra_val if extra_val in ("under_warranty", "expired", "expiring_soon") else "all"
                data = report_service.get_warranty_report_data(db, warranty_filter=w_filter, department_id=dept_id)
                summary = data["summary"]
                self.stat_card_1.set_title("إجمالي الأجهزة المفحوصة")
                self.stat_card_1.set_value(f"{summary.get('total_count', 0):,}")
                self.stat_card_2.set_title("ساري الضمان")
                self.stat_card_2.set_value(f"{summary.get('under_warranty_count', 0):,}")
                self.stat_card_3.set_title("منتهي الضمان")
                self.stat_card_3.set_value(f"{summary.get('expired_count', 0):,}")
                self.stat_card_4.set_title("القسم الطبي")
                self.stat_card_4.set_value(self.dept_combo.currentText())

            elif rtype == "equipment_history":
                eq_id = extra_val if isinstance(extra_val, int) else None
                if not eq_id and self.dynamic_combo.count() > 0:
                    eq_id = self.dynamic_combo.itemData(0)
                if eq_id:
                    data = report_service.get_equipment_history_report_data(db, equipment_id=eq_id)
                    summary = data.get("summary", {})
                    self.stat_card_1.set_title("إجمالي أوامر الصيانة")
                    self.stat_card_1.set_value(f"{summary.get('total_orders', 0):,}")
                    self.stat_card_2.set_title("البلاغات المكتملة")
                    self.stat_card_2.set_value(f"{summary.get('completed_orders', 0):,}")
                    self.stat_card_3.set_title("إجمالي تكلفة الصيانة")
                    self.stat_card_3.set_value(f"{summary.get('total_maint_cost', 0):,.2f} ر.س")
                    self.stat_card_4.set_title("نسبة الصيانة للشراء")
                    self.stat_card_4.set_value(f"{summary.get('cost_ratio', 0):.1f}%")
                else:
                    data = {"title": "تقرير صيانة الجهاز", "headers": [], "column_keys": [], "rows": [], "summary": {}}

            else:  # periodic_maintenance
                data = report_service.get_periodic_maintenance_report_data(
                    db, from_date=from_d, to_date=to_d, department_id=dept_id
                )
                summary = data["summary"]
                self.stat_card_1.set_title("إجمالي البلاغات المسجلة")
                self.stat_card_1.set_value(f"{summary.get('total_orders', 0):,}")
                self.stat_card_2.set_title("البلاغات المنجزة")
                self.stat_card_2.set_value(f"{summary.get('completed_orders', 0):,}")
                self.stat_card_3.set_title("قيد التنفيذ / متأخر")
                self.stat_card_3.set_value(f"{summary.get('total_orders', 0) - summary.get('completed_orders', 0):,}")
                self.stat_card_4.set_title("التكلفة الإجمالية للصيانة")
                self.stat_card_4.set_value(f"{summary.get('total_cost', 0):,.0f} ر.س")

        self.current_report_data = data
        self._render_table(data)

    def _render_table(self, data: dict):
        headers = data.get("headers", [])
        column_keys = data.get("column_keys", [])
        rows = data.get("rows", [])

        self.table_widget.set_headers(headers)
        table = self.table_widget.table
        table.setRowCount(len(rows))

        for r_idx, row in enumerate(rows):
            for c_idx, col_key in enumerate(column_keys):
                val = row.get(col_key, "—")
                if isinstance(val, float):
                    val_str = f"{val:,.2f} ر.س" if ("cost" in col_key or "price" in col_key or "value" in col_key) else f"{val:,.2f}"
                else:
                    val_str = str(val if val is not None else "—")
                item = QTableWidgetItem(val_str)
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                table.setItem(r_idx, c_idx, item)

        self.table_widget.set_record_count(len(rows), len(rows))

        rtype = self.report_type_combo.currentData()
        if rtype == "equipment":
            widths = [125, 175, 120, 120, 155, 135, 110, 100, 115, 115]
            stretches = [1, 4]
        elif rtype == "work_orders":
            widths = [110, 160, 100, 110, 100, 120, 180, 100, 100, 100, 110]
            stretches = [1, 5, 6]
        elif rtype == "pm_compliance":
            widths = [105, 160, 160, 110, 100, 120, 105, 180]
            stretches = [1, 2, 7]
        elif rtype == "inventory":
            widths = [110, 180, 140, 105, 105, 105, 110, 110, 140]
            stretches = [1, 2]
        elif rtype == "manufacturer":
            widths = [150, 110, 165, 120, 120, 130, 105, 105, 115]
            stretches = [0, 2]
        elif rtype == "vendor_agent":
            widths = [150, 120, 110, 165, 120, 135, 115, 105, 100]
            stretches = [0, 3]
        elif rtype == "category":
            widths = [125, 175, 155, 120, 120, 110, 100, 115]
            stretches = [1, 2]
        elif rtype == "department_summary":
            widths = [165, 100, 120, 120, 120, 130, 130]
            stretches = [0]
        elif rtype == "warranty":
            widths = [115, 165, 120, 120, 130, 135, 120, 105, 125]
            stretches = [1, 5]
        elif rtype == "periodic_maintenance":
            widths = [115, 105, 165, 130, 100, 105, 135, 180, 110]
            stretches = [2, 7]
        else:
            widths = [130] * len(headers)
            stretches = [1] if len(headers) > 1 else []

        self.table_widget.set_column_widths(widths, stretch_cols=stretches)
        self.table_widget.table.verticalHeader().setDefaultSectionSize(38)

    def _on_search(self, query: str):
        query = query.lower().strip()
        rows = self.current_report_data.get("rows", [])
        column_keys = self.current_report_data.get("column_keys", [])

        if not query:
            filtered_rows = rows
        else:
            filtered_rows = [
                r for r in rows
                if any(query in str(v).lower() for v in r.values())
            ]

        table = self.table_widget.table
        table.setRowCount(len(filtered_rows))

        for r_idx, row in enumerate(filtered_rows):
            for c_idx, col_key in enumerate(column_keys):
                val = row.get(col_key, "—")
                if isinstance(val, float):
                    val_str = f"{val:,.2f} ر.س" if ("cost" in col_key or "price" in col_key or "value" in col_key) else f"{val:,.2f}"
                else:
                    val_str = str(val if val is not None else "—")
                item = QTableWidgetItem(val_str)
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                table.setItem(r_idx, c_idx, item)

        self.table_widget.set_record_count(len(filtered_rows), len(rows))

    def _print_report(self):
        if not self.current_report_data or not self.current_report_data.get("rows"):
            QMessageBox.warning(self, "تنبيه", "لا توجد بيانات متاحة للطباعة أو المعاينة.")
            return

        try:
            html = report_service.generate_html_report(self.current_report_data)

            printer = QPrinter(QPrinter.PrinterMode.ScreenResolution)
            orientation = report_service.get_page_orientation(self.current_report_data)
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
            preview.setWindowTitle("معاينة التقرير قبل الطباعة — هيئة مستشفى الثورة بصنعاء")
            preview.resize(1100, 780)
            preview.paintRequested.connect(_paint_preview)
            preview.exec()
        except Exception as e:
            QMessageBox.critical(self, "خطأ في الطباعة", f"فشل فتح معاينة الطباعة: {str(e)}")

    def _export_excel(self):
        if not self.current_report_data or not self.current_report_data.get("rows"):
            QMessageBox.warning(self, "تنبيه", "لا توجد بيانات متاحة للتصدير.")
            return

        rtype = self.report_type_combo.currentData()
        def_name = f"MEMMS_Report_{rtype}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        path, _ = QFileDialog.getSaveFileName(
            self, "تصدير تقرير إلى Excel", def_name, "Excel Files (*.xlsx)"
        )
        if not path:
            return

        try:
            report_service.export_to_excel(self.current_report_data, path)
            QMessageBox.information(
                self, "تم بنجاح",
                f"تم تصدير ملف Excel بنجاح إلى المسار:\n{path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل تصدير Excel: {str(e)}")

    def _export_pdf(self):
        if not self.current_report_data or not self.current_report_data.get("rows"):
            QMessageBox.warning(self, "تنبيه", "لا توجد بيانات متاحة للتصدير.")
            return

        rtype = self.report_type_combo.currentData()
        def_name = f"MEMMS_Report_{rtype}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        path, _ = QFileDialog.getSaveFileName(
            self, "تصدير تقرير إلى PDF", def_name, "PDF Files (*.pdf)"
        )
        if not path:
            return

        try:
            html = report_service.generate_html_report(self.current_report_data)

            writer = QPdfWriter(path)
            writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
            orientation = report_service.get_page_orientation(self.current_report_data)
            writer.setPageOrientation(
                QPageLayout.Orientation.Landscape if orientation == "landscape"
                else QPageLayout.Orientation.Portrait
            )
            writer.setPageMargins(QMarginsF(10, 10, 10, 10), QPageLayout.Unit.Millimeter)
            writer.setResolution(96)

            paint_rect = writer.pageLayout().paintRectPixels(writer.resolution())
            doc = QTextDocument()
            doc.setPageSize(QSizeF(paint_rect.width(), paint_rect.height()))
            report_service.prepare_rtl_document(doc, html, font_size=10)
            doc.print_(writer)

            QMessageBox.information(
                self, "تم بنجاح",
                f"تم إنشاء وتصدير ملف PDF باللغة العربية بنجاح إلى:\n{path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل تصدير PDF: {str(e)}")

    def _export_csv(self):
        if not self.current_report_data or not self.current_report_data.get("rows"):
            QMessageBox.warning(self, "تنبيه", "لا توجد بيانات متاحة للتصدير.")
            return

        rtype = self.report_type_combo.currentData()
        def_name = f"MEMMS_Report_{rtype}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        path, _ = QFileDialog.getSaveFileName(
            self, "تصدير CSV", def_name, "CSV Files (*.csv)"
        )
        if not path:
            return

        try:
            report_service.export_to_csv(self.current_report_data, path)
            QMessageBox.information(
                self, "تم بنجاح",
                f"تم تصدير ملف CSV بنجاح إلى:\n{path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل تصدير CSV: {str(e)}")

    def retranslate_ui(self):
        self.refresh_data()
