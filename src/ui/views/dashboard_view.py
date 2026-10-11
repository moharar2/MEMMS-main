"""
Enterprise Dashboard View for MEMMS:
Laptop-optimized, ultra-clean executive overview, KPI metrics, fleet readiness index, and quick actions.
Pure Arabic, RTL, zero emojis, responsive and compact.
"""
from datetime import datetime, date
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QProgressBar, QGridLayout, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QTimer
from src.core.i18n import tr
from src.core.database import get_db
from src.services.equipment_service import equipment_service
from src.services.pm_service import pm_service
from src.models.equipment import Equipment
from src.models.work_order import WorkOrder
from src.models.inventory import SparePart
from src.ui.theme.icons import icon


class CompactStatCard(QFrame):
    """Compact, laptop-friendly KPI card."""
    def __init__(self, title: str, value: str, icon_name: str, accent_color: str, subtitle: str = None, parent=None):
        super().__init__(parent)
        self.accent_color = accent_color
        self.setFixedHeight(72)
        self.setStyleSheet(f"""
            CompactStatCard {{
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
            }}
            CompactStatCard:hover {{
                border-color: {accent_color};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # Icon
        self.icon_box = QLabel()
        self.icon_box.setFixedSize(36, 36)
        self.icon_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_box.setPixmap(icon(icon_name, color=accent_color, size=18).pixmap(18, 18))
        self.icon_box.setStyleSheet(f"""
            background-color: {accent_color}14;
            border-radius: 6px;
            border: 1px solid {accent_color}25;
        """)
        layout.addWidget(self.icon_box)

        # Texts
        text_layout = QVBoxLayout()
        text_layout.setSpacing(1)
        text_layout.setContentsMargins(0, 0, 0, 0)

        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748B;")
        text_layout.addWidget(self.title_lbl)

        val_box = QHBoxLayout()
        val_box.setSpacing(6)
        val_box.setContentsMargins(0, 0, 0, 0)

        self.val_lbl = QLabel(str(value))
        self.val_lbl.setStyleSheet("font-size: 18px; font-weight: 800; color: #0F172A;")
        val_box.addWidget(self.val_lbl)

        if subtitle:
            self.sub_lbl = QLabel(subtitle)
            self.sub_lbl.setStyleSheet("font-size: 10px; color: #94A3B8; font-weight: 600;")
            val_box.addWidget(self.sub_lbl)
        else:
            self.sub_lbl = None

        val_box.addStretch()
        text_layout.addLayout(val_box)
        layout.addLayout(text_layout)
        layout.addStretch()

    def set_value(self, value: any):
        self.val_lbl.setText(str(value))

    def set_subtitle(self, text: str):
        if self.sub_lbl:
            self.sub_lbl.setText(text)


class CompactProgressRow(QWidget):
    """Clean, tight progress bar row fitting comfortably on smaller screens."""
    def __init__(self, label: str, count: int, total: int, bar_color: str, unit: str = "جهاز", parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 3, 0, 3)
        layout.setSpacing(3)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(6)

        dot = QLabel()
        dot.setFixedSize(7, 7)
        dot.setStyleSheet(f"background-color: {bar_color}; border-radius: 3.5px;")
        header_layout.addWidget(dot)

        lbl = QLabel(label)
        lbl.setStyleSheet("font-size: 12px; font-weight: 700; color: #334155;")
        header_layout.addWidget(lbl)
        header_layout.addStretch()

        pct = round((count / total * 100), 1) if total > 0 else 0.0
        val_lbl = QLabel(f"{count} {unit} ({pct}%)")
        val_lbl.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {bar_color};")
        header_layout.addWidget(val_lbl)
        layout.addLayout(header_layout)

        pbar = QProgressBar()
        pbar.setRange(0, 100)
        pbar.setValue(int(pct))
        pbar.setTextVisible(False)
        pbar.setFixedHeight(5)
        pbar.setStyleSheet(f"""
            QProgressBar {{
                background-color: #F1F5F9;
                border: none;
                border-radius: 2.5px;
            }}
            QProgressBar::chunk {{
                background-color: {bar_color};
                border-radius: 2.5px;
            }}
        """)
        layout.addWidget(pbar)


class CompactActionBtn(QPushButton):
    """Sleek modern action button for bottom hub."""
    def __init__(self, title: str, subtitle: str, icon_name: str, accent_color: str, parent=None):
        super().__init__("", parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(46)
        self.setStyleSheet(f"""
            CompactActionBtn {{
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
            }}
            CompactActionBtn:hover {{
                background-color: #F8FAFC;
                border-color: {accent_color};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(10)

        ic_lbl = QLabel()
        ic_lbl.setPixmap(icon(icon_name, color=accent_color, size=16).pixmap(16, 16))
        layout.addWidget(ic_lbl)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(0)
        text_layout.setContentsMargins(0, 0, 0, 0)

        t_lbl = QLabel(title)
        t_lbl.setStyleSheet("font-size: 12px; font-weight: 800; color: #0F172A;")
        s_lbl = QLabel(subtitle)
        s_lbl.setStyleSheet("font-size: 10px; color: #64748B; font-weight: 500;")

        text_layout.addWidget(t_lbl)
        text_layout.addWidget(s_lbl)
        layout.addLayout(text_layout)
        layout.addStretch()


class DashboardView(QWidget):
    navigate_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll area with smooth laptop sizing
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background-color: transparent;")

        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(18, 14, 18, 14)
        main_layout.setSpacing(12)

        # ── 1. Compact Header Banner ─────────────────────────────────────────
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                padding: 10px 14px;
            }
        """)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(12)

        titles_box = QVBoxLayout()
        titles_box.setSpacing(2)

        self.title_lbl = QLabel("لوحة المؤشرات والجاهزية التشغيلية")
        self.title_lbl.setStyleSheet("font-size: 16px; font-weight: 800; color: #0F172A;")

        self.subtitle_lbl = QLabel("متابعة فورية ومباشرة للأجهزة الطبية، بلاغات الصيانة، ونسب الامتثال للفحص الوقائي والمعايرة")
        self.subtitle_lbl.setStyleSheet("font-size: 11px; color: #64748B; font-weight: 500;")

        titles_box.addWidget(self.title_lbl)
        titles_box.addWidget(self.subtitle_lbl)
        header_layout.addLayout(titles_box)
        header_layout.addStretch()

        # Action Buttons
        btn_box = QHBoxLayout()
        btn_box.setSpacing(8)

        self.refresh_btn = QPushButton("تحديث البيانات")
        self.refresh_btn.setIcon(icon("refresh", color="#0F766E", size=13))
        self.refresh_btn.setFixedHeight(34)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #334155;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
                padding: 4px 12px;
            }
            QPushButton:hover {
                background-color: #F8FAFC;
                border-color: #94A3B8;
                color: #0F172A;
            }
        """)
        self.refresh_btn.clicked.connect(self.refresh)
        btn_box.addWidget(self.refresh_btn)

        self.add_eq_btn = QPushButton("+ إضافة جهاز")
        self.add_eq_btn.setIcon(icon("equipment", color="#0F766E", size=13))
        self.add_eq_btn.setFixedHeight(34)
        self.add_eq_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #334155;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
                padding: 4px 12px;
            }
            QPushButton:hover {
                background-color: #F8FAFC;
                border-color: #94A3B8;
                color: #0F172A;
            }
        """)
        self.add_eq_btn.clicked.connect(lambda: self.navigate_requested.emit("equipment"))
        btn_box.addWidget(self.add_eq_btn)

        self.wo_btn = QPushButton("+ فتح بلاغ صيانة")
        self.wo_btn.setIcon(icon("add", color="#FFFFFF", size=13))
        self.wo_btn.setFixedHeight(34)
        self.wo_btn.setStyleSheet("""
            QPushButton {
                background-color: #0F766E;
                color: #FFFFFF;
                border: 1px solid #0F766E;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 700;
                padding: 4px 14px;
            }
            QPushButton:hover {
                background-color: #0D9488;
                border-color: #0D9488;
            }
            QPushButton:pressed {
                background-color: #115E59;
            }
        """)
        self.wo_btn.clicked.connect(lambda: self.navigate_requested.emit("work_orders"))
        btn_box.addWidget(self.wo_btn)

        header_layout.addLayout(btn_box)
        main_layout.addWidget(header_frame)

        # ── 2. Top KPI Cards Row (4 Primary Executive Cards) ─────────────────
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(10)

        self.card_total = CompactStatCard("إجمالي الأجهزة الطبية", "0", "equipment", "#0F766E")
        self.card_op = CompactStatCard("جاهزة وتعمل بكفاءة", "0", "check", "#059669")
        self.card_maint = CompactStatCard("تحت الصيانة والإصلاح", "0", "work_orders", "#D97706")
        self.card_urgent = CompactStatCard("بلاغات حرجة / متأخرة", "0", "warning", "#DC2626")

        stats_layout.addWidget(self.card_total)
        stats_layout.addWidget(self.card_op)
        stats_layout.addWidget(self.card_maint)
        stats_layout.addWidget(self.card_urgent)
        main_layout.addLayout(stats_layout)

        # ── 3. Main Analytics Cards (2 Balanced Columns) ─────────────────────
        analytics_layout = QHBoxLayout()
        analytics_layout.setSpacing(10)

        # Card 1: Equipment Fleet Readiness
        self.readiness_card = QFrame()
        self.readiness_card.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                padding: 12px 14px;
            }
        """)
        c1_layout = QVBoxLayout(self.readiness_card)
        c1_layout.setSpacing(8)

        c1_header = QHBoxLayout()
        c1_title = QLabel("مؤشر الجاهزية التشغيلية للأسطول الطبي")
        c1_title.setStyleSheet("font-size: 13px; font-weight: 800; color: #0F172A;")
        self.readiness_badge = QLabel("100% جاهزية")
        self.readiness_badge.setStyleSheet("""
            background-color: #ECFDF5;
            color: #059669;
            font-size: 11px;
            font-weight: 800;
            padding: 2px 8px;
            border-radius: 4px;
            border: 1px solid #A7F3D0;
        """)
        c1_header.addWidget(c1_title)
        c1_header.addStretch()
        c1_header.addWidget(self.readiness_badge)
        c1_layout.addLayout(c1_header)

        self.readiness_rows = QVBoxLayout()
        self.readiness_rows.setSpacing(2)
        c1_layout.addLayout(self.readiness_rows)
        c1_layout.addStretch()

        analytics_layout.addWidget(self.readiness_card, stretch=1)

        # Card 2: Work Orders & Priority Response
        self.wo_card = QFrame()
        self.wo_card.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                padding: 12px 14px;
            }
        """)
        c2_layout = QVBoxLayout(self.wo_card)
        c2_layout.setSpacing(8)

        c2_header = QHBoxLayout()
        c2_title = QLabel("توزيع بلاغات وأوامر الصيانة حسب الأولوية")
        c2_title.setStyleSheet("font-size: 13px; font-weight: 800; color: #0F172A;")
        self.wo_active_badge = QLabel("0 بلاغ نشط")
        self.wo_active_badge.setStyleSheet("""
            background-color: #EFF6FF;
            color: #2563EB;
            font-size: 11px;
            font-weight: 800;
            padding: 2px 8px;
            border-radius: 4px;
            border: 1px solid #BFDBFE;
        """)
        c2_header.addWidget(c2_title)
        c2_header.addStretch()
        c2_header.addWidget(self.wo_active_badge)
        c2_layout.addLayout(c2_header)

        self.wo_priority_rows = QVBoxLayout()
        self.wo_priority_rows.setSpacing(2)
        c2_layout.addLayout(self.wo_priority_rows)
        c2_layout.addStretch()

        analytics_layout.addWidget(self.wo_card, stretch=1)
        main_layout.addLayout(analytics_layout)

        # ── 4. Secondary Operational Indicators (3 Compact Cards) ───────────
        sec_layout = QHBoxLayout()
        sec_layout.setSpacing(10)

        # Mini Card A: PM Compliance
        card_a = QFrame()
        card_a.setStyleSheet("background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 10px 12px;")
        ca_layout = QVBoxLayout(card_a)
        ca_layout.setSpacing(4)
        
        ca_head = QHBoxLayout()
        ca_t = QLabel("الصيانة الوقائية والمعايرة")
        ca_t.setStyleSheet("font-size: 12px; font-weight: 800; color: #0F172A;")
        self.pm_badge = QLabel("100% امتثال")
        self.pm_badge.setStyleSheet("font-size: 10px; font-weight: 700; color: #16A34A; background: #F0FDF4; padding: 2px 6px; border-radius: 4px;")
        ca_head.addWidget(ca_t)
        ca_head.addStretch()
        ca_head.addWidget(self.pm_badge)
        ca_layout.addLayout(ca_head)
        
        self.pm_detail_lbl = QLabel("0 فحص مجدول | 0 متأخر")
        self.pm_detail_lbl.setStyleSheet("font-size: 11px; color: #475569; font-weight: 600;")
        ca_layout.addWidget(self.pm_detail_lbl)
        sec_layout.addWidget(card_a, stretch=1)

        # Mini Card B: Spare Parts & Inventory
        card_b = QFrame()
        card_b.setStyleSheet("background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 10px 12px;")
        cb_layout = QVBoxLayout(card_b)
        cb_layout.setSpacing(4)
        
        cb_head = QHBoxLayout()
        cb_t = QLabel("قطع الغيار والمخزون")
        cb_t.setStyleSheet("font-size: 12px; font-weight: 800; color: #0F172A;")
        self.inv_badge = QLabel("مكتمل")
        self.inv_badge.setStyleSheet("font-size: 10px; font-weight: 700; color: #7C3AED; background: #F5F3FF; padding: 2px 6px; border-radius: 4px;")
        cb_head.addWidget(cb_t)
        cb_head.addStretch()
        cb_head.addWidget(self.inv_badge)
        cb_layout.addLayout(cb_head)
        
        self.inv_detail_lbl = QLabel("مستويات المخزون آمنة")
        self.inv_detail_lbl.setStyleSheet("font-size: 11px; color: #475569; font-weight: 600;")
        cb_layout.addWidget(self.inv_detail_lbl)
        sec_layout.addWidget(card_b, stretch=1)

        # Mini Card C: Risk Classification
        card_c = QFrame()
        card_c.setStyleSheet("background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 10px 12px;")
        cc_layout = QVBoxLayout(card_c)
        cc_layout.setSpacing(4)
        
        cc_head = QHBoxLayout()
        cc_t = QLabel("تصنيف الخطورة الإكلينيكية")
        cc_t.setStyleSheet("font-size: 12px; font-weight: 800; color: #0F172A;")
        cc_head.addWidget(cc_t)
        cc_head.addStretch()
        cc_layout.addLayout(cc_head)
        
        self.risk_detail_lbl = QLabel("0 عالي | 0 متوسط | 0 منخفض")
        self.risk_detail_lbl.setStyleSheet("font-size: 11px; color: #475569; font-weight: 600;")
        cc_layout.addWidget(self.risk_detail_lbl)
        sec_layout.addWidget(card_c, stretch=1)

        main_layout.addLayout(sec_layout)

        # ── 5. Quick Navigation Action Bar ───────────────────────────────────
        hub_layout = QHBoxLayout()
        hub_layout.setSpacing(10)

        self.btn_nav_wo = CompactActionBtn("أوامر الصيانة والبلاغات", "متابعة البلاغات وتكليف المهندسين", "work_orders", "#0F766E")
        self.btn_nav_wo.clicked.connect(lambda: self.navigate_requested.emit("work_orders"))

        self.btn_nav_pm = CompactActionBtn("الصيانة الوقائية والمعايرة", "جداول المعايرة والفحص الدوري", "preventive", "#2563EB")
        self.btn_nav_pm.clicked.connect(lambda: self.navigate_requested.emit("preventive"))

        self.btn_nav_inv = CompactActionBtn("مستودع قطع الغيار", "أرصدة المخزون وحركات الصرف", "inventory", "#7C3AED")
        self.btn_nav_inv.clicked.connect(lambda: self.navigate_requested.emit("inventory"))

        self.btn_nav_rep = CompactActionBtn("التقارير التحليلية", "تصدير السجلات إلى Excel و PDF", "reports", "#D97706")
        self.btn_nav_rep.clicked.connect(lambda: self.navigate_requested.emit("reports"))

        hub_layout.addWidget(self.btn_nav_wo)
        hub_layout.addWidget(self.btn_nav_pm)
        hub_layout.addWidget(self.btn_nav_inv)
        hub_layout.addWidget(self.btn_nav_rep)
        main_layout.addLayout(hub_layout)

        scroll.setWidget(container)
        outer_layout.addWidget(scroll)

        QTimer.singleShot(0, self.refresh)

    def refresh(self):
        with get_db() as db:
            # 1. Total equipment metrics
            stats = equipment_service.get_equipment_stats(db)
            total = stats.get("total", 0)
            op = stats.get("operational", 0)
            maint = stats.get("under_maintenance", 0)
            out = stats.get("out_of_service", 0)
            standby = stats.get("standby", 0)

            self.card_total.set_value(str(total))
            self.card_op.set_value(str(op))
            self.card_maint.set_value(str(maint))

            readiness_pct = round((op / total * 100), 1) if total > 0 else 100.0
            self.readiness_badge.setText(f"{readiness_pct}% جاهزية الأسطول")

            # 2. PM metrics
            pm_stats = pm_service.get_pm_statistics(db)
            pm_total = pm_stats.get("total_schedules", 0)
            pm_scheduled = pm_stats.get("scheduled", 0)
            pm_overdue = pm_stats.get("overdue", 0)

            pm_compliance = round(((pm_total - pm_overdue) / pm_total * 100), 1) if pm_total > 0 else 100.0
            self.pm_badge.setText(f"{pm_compliance}% امتثال")
            self.pm_detail_lbl.setText(f"{pm_scheduled} مجدول | {pm_overdue} متأخر")

            # 3. Inventory low stock count
            low_parts_count = db.query(SparePart).filter(
                SparePart.quantity_on_hand <= SparePart.minimum_reorder_level,
                SparePart.is_active == True
            ).count()

            if low_parts_count > 0:
                self.inv_badge.setText(f"{low_parts_count} نواقص")
                self.inv_badge.setStyleSheet("font-size: 10px; font-weight: 700; color: #DC2626; background: #FEF2F2; padding: 2px 6px; border-radius: 4px;")
                self.inv_detail_lbl.setText(f"يوجد {low_parts_count} أصناف أوشكت على النفاد")
            else:
                self.inv_badge.setText("مكتمل")
                self.inv_badge.setStyleSheet("font-size: 10px; font-weight: 700; color: #059669; background: #ECFDF5; padding: 2px 6px; border-radius: 4px;")
                self.inv_detail_lbl.setText("كافة أرصدة المخزون آمنة")

            # 4. Work Orders stats
            critical_wo = db.query(WorkOrder).filter(
                WorkOrder.priority == "critical",
                WorkOrder.status.in_(["pending", "assigned", "in_progress", "waiting_parts"])
            ).count()
            high_wo = db.query(WorkOrder).filter(
                WorkOrder.priority == "high",
                WorkOrder.status.in_(["pending", "assigned", "in_progress", "waiting_parts"])
            ).count()
            medium_wo = db.query(WorkOrder).filter(
                WorkOrder.priority == "medium",
                WorkOrder.status.in_(["pending", "assigned", "in_progress", "waiting_parts"])
            ).count()
            low_wo = db.query(WorkOrder).filter(
                WorkOrder.priority == "low",
                WorkOrder.status.in_(["pending", "assigned", "in_progress", "waiting_parts"])
            ).count()

            active_wo_count = critical_wo + high_wo + medium_wo + low_wo
            self.card_urgent.set_value(str(critical_wo + pm_overdue))
            self.wo_active_badge.setText(f"{active_wo_count} بلاغ نشط")

            # 5. Populate Readiness Breakdown Rows
            self._clear_layout(self.readiness_rows)
            self.readiness_rows.addWidget(CompactProgressRow("جاهز ويعمل بكفاءة كاملة", op, total, "#059669"))
            self.readiness_rows.addWidget(CompactProgressRow("تحت الصيانة والإصلاح الفني", maint, total, "#D97706"))
            self.readiness_rows.addWidget(CompactProgressRow("خارج الخدمة / معطل", out, total, "#DC2626"))
            self.readiness_rows.addWidget(CompactProgressRow("في وضع الجاهزية والاستعداد", standby, total, "#0284C7"))

            # 6. Populate Work Order Priority Rows
            self._clear_layout(self.wo_priority_rows)
            self.wo_priority_rows.addWidget(CompactProgressRow("بلاغات حرجة وطارئة جداً", critical_wo, active_wo_count, "#DC2626", "بلاغ"))
            self.wo_priority_rows.addWidget(CompactProgressRow("بلاغات أولوية عالية", high_wo, active_wo_count, "#D97706", "بلاغ"))
            self.wo_priority_rows.addWidget(CompactProgressRow("بلاغات أولوية متوسطة", medium_wo, active_wo_count, "#2563EB", "بلاغ"))
            self.wo_priority_rows.addWidget(CompactProgressRow("بلاغات روتينية وعادية", low_wo, active_wo_count, "#059669", "بلاغ"))

            # 7. Risk Classification
            risk_high = db.query(Equipment).filter(Equipment.risk_level == "high").count()
            risk_med = db.query(Equipment).filter(Equipment.risk_level == "medium").count()
            risk_low = db.query(Equipment).filter(Equipment.risk_level == "low").count()
            self.risk_detail_lbl.setText(f"{risk_high} عالي | {risk_med} متوسط | {risk_low} منخفض")

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def retranslate_ui(self):
        self.refresh()
