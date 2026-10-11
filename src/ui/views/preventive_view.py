"""
Preventive Maintenance View (PM).
Displays recurring schedules, overdue warnings, protocol checklists,
and compliance inspection execution. Zero emojis, vector icons, bilingual support.
"""
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QComboBox, QMessageBox, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt, Signal, QTimer
from src.core.i18n import tr
from src.core.database import get_db
from src.models.preventive import PMSchedule, PMPlan, PMExecution
from src.services.pm_service import pm_service
from src.ui.theme.icons import icon
from src.ui.components.stat_card import StatCard
from src.ui.components.status_badge import StatusBadge
from src.ui.components.data_table import DataTable
from src.ui.components.confirm_dialog import confirm_action
from src.ui.components.action_button import ActionButton, create_actions_cell
from src.ui.views.pm_plan_dialog import PMPlanDialog
from src.ui.views.pm_execution_dialog import PMExecutionDialog


class PreventiveView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        QTimer.singleShot(0, self.refresh_data)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 14, 18, 14)
        main_layout.setSpacing(10)

        # 1. Header & Actions
        header_layout = QHBoxLayout()
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)

        self.title_lbl = QLabel(tr("pm.title"))
        self.title_lbl.setStyleSheet("font-size: 18px; font-weight: 800; color: #0F172A;")
        self.sub_lbl = QLabel(tr("pm.subtitle"))
        self.sub_lbl.setStyleSheet("font-size: 12px; color: #64748B;")
        title_layout.addWidget(self.title_lbl)
        title_layout.addWidget(self.sub_lbl)
        header_layout.addLayout(title_layout)
        header_layout.addStretch()

        self.gen_btn = QPushButton(tr("pm.generate_schedules"))
        self.gen_btn.setIcon(icon("refresh", color="#0F766E", size=15))
        self.gen_btn.clicked.connect(self._generate_all_schedules)
        header_layout.addWidget(self.gen_btn)

        self.add_plan_btn = QPushButton(tr("pm.new_plan"))
        self.add_plan_btn.setObjectName("primaryBtn")
        self.add_plan_btn.setIcon(icon("add", color="#FFFFFF", size=15))
        self.add_plan_btn.clicked.connect(self._open_new_plan_dialog)
        header_layout.addWidget(self.add_plan_btn)

        main_layout.addLayout(header_layout)

        # 2. KPI Stat Cards
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(10)

        self.card_total = StatCard(tr("pm.total_schedules"), "0", icon_name="schedule", accent_color="#0F766E")
        self.card_scheduled = StatCard(tr("pm.scheduled_count"), "0", icon_name="calendar", accent_color="#2563EB")
        self.card_overdue = StatCard(tr("pm.overdue_count"), "0", icon_name="warning", accent_color="#EF4444")
        self.card_completed = StatCard(tr("pm.completed_count"), "0", icon_name="check_double", accent_color="#10B981")
        for card in (self.card_total, self.card_scheduled, self.card_overdue, self.card_completed):
            card.setFixedHeight(72)

        kpi_layout.addWidget(self.card_total)
        kpi_layout.addWidget(self.card_scheduled)
        kpi_layout.addWidget(self.card_overdue)
        kpi_layout.addWidget(self.card_completed)
        main_layout.addLayout(kpi_layout)

        # 3. Main Tabs: Schedules vs Plans
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                background-color: #FFFFFF;
                top: -1px;
            }
            QTabBar::tab {
                background: #F1F5F9;
                color: #64748B;
                padding: 8px 16px;
                font-weight: 600;
                font-size: 12px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 4px;
            }
            QTabBar::tab:selected {
                background: #FFFFFF;
                color: #0F766E;
                border: 1px solid #E2E8F0;
                border-bottom: 2px solid #0F766E;
            }
        """)

        # Tab 1: Schedules Table
        schedules_widget = QWidget()
        schedules_layout = QVBoxLayout(schedules_widget)
        schedules_layout.setContentsMargins(8, 10, 8, 10)
        schedules_layout.setSpacing(8)

        # Status filter for schedules
        sched_filter_layout = QHBoxLayout()
        self.status_filter = QComboBox()
        self.status_filter.addItem(tr("common.all"), "all")
        self.status_filter.addItem(tr("pm.status_scheduled"), "scheduled")
        self.status_filter.addItem(tr("pm.status_overdue"), "overdue")
        self.status_filter.addItem(tr("pm.status_completed"), "completed")
        self.status_filter.currentIndexChanged.connect(self._load_schedules)

        sched_filter_layout.addWidget(QLabel(tr("common.status") + ":"))
        sched_filter_layout.addWidget(self.status_filter)
        sched_filter_layout.addStretch()
        schedules_layout.addLayout(sched_filter_layout)

        self.schedules_table = DataTable()
        self.schedules_table.set_add_button_visible(False)
        self.schedules_table.set_search_placeholder(tr("common.search"))
        self.schedules_table.search_changed.connect(self._on_search_schedules)
        self.schedules_table.refresh_requested.connect(self.refresh_data)

        sched_headers = [
            "#",
            tr("equipment.asset_id"),
            tr("equipment.name"),
            tr("departments.title"),
            tr("pm.plan_title"),
            tr("pm.due_date"),
            tr("common.status"),
            tr("common.actions")
        ]
        self.schedules_table.set_headers(sched_headers)
        # 0: ID, 1: Asset#, 2: Name, 3: Dept, 4: Plan, 5: Due, 6: Status, 7: Actions
        self.schedules_table.set_column_widths([50, 110, 180, 140, 170, 100, 100, 90], stretch_cols=[2, 3, 4])
        self.schedules_table.table.verticalHeader().setDefaultSectionSize(38)
        schedules_layout.addWidget(self.schedules_table)
        self.tabs.addTab(schedules_widget, tr("pm.tab_schedules"))

        # Tab 2: PM Protocols / Plans Table
        plans_widget = QWidget()
        plans_layout = QVBoxLayout(plans_widget)
        plans_layout.setContentsMargins(8, 10, 8, 10)
        plans_layout.setSpacing(8)

        self.plans_table = DataTable()
        self.plans_table.set_add_button_text(tr("pm.new_plan"))
        self.plans_table.add_requested.connect(self._open_new_plan_dialog)
        self.plans_table.set_search_placeholder(tr("common.search"))
        self.plans_table.search_changed.connect(self._on_search_plans)
        self.plans_table.refresh_requested.connect(self.refresh_data)

        plan_headers = [
            "#",
            tr("pm.plan_title"),
            tr("pm.target_category"),
            tr("pm.frequency_days"),
            tr("pm.estimated_duration"),
            tr("pm.checklist"),
            tr("common.actions")
        ]
        self.plans_table.set_headers(plan_headers)
        # 0: ID, 1: Title, 2: Target, 3: Freq, 4: Dur, 5: Check, 6: Actions
        self.plans_table.set_column_widths([50, 200, 150, 100, 100, 120, 80], stretch_cols=[1, 2])
        self.plans_table.table.verticalHeader().setDefaultSectionSize(38)
        plans_layout.addWidget(self.plans_table)
        self.tabs.addTab(plans_widget, tr("pm.tab_plans"))

        main_layout.addWidget(self.tabs, stretch=1)

    def refresh_data(self):
        self._load_kpis()
        self._load_schedules()
        self._load_plans()

    def _load_kpis(self):
        with get_db() as db:
            stats = pm_service.get_pm_statistics(db)
            self.card_total.set_value(str(stats["total_schedules"]))
            self.card_scheduled.set_value(str(stats["scheduled"]))
            self.card_overdue.set_value(str(stats["overdue"]))
            self.card_completed.set_value(str(stats["completed_this_month"]))

    def _load_schedules(self):
        status = self.status_filter.currentData()
        with get_db() as db:
            schedules = pm_service.list_schedules(db, status=status)
            self.all_schedules = schedules
            self._render_schedules(schedules)

    def _render_schedules(self, schedules):
        table = self.schedules_table.table
        table.setRowCount(len(schedules))

        for row, s in enumerate(schedules):
            eq = s.equipment
            plan = s.plan
            dept_name = eq.department.name_ar if eq and eq.department else "-"

            it_id = QTableWidgetItem(str(s.id))
            it_id.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            table.setItem(row, 0, it_id)

            it_asset = QTableWidgetItem(eq.asset_number if eq else "-")
            it_asset.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            table.setItem(row, 1, it_asset)

            it_name = QTableWidgetItem(eq.name_ar or eq.name_en if eq else "-")
            it_name.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            table.setItem(row, 2, it_name)

            it_dept = QTableWidgetItem(dept_name)
            it_dept.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            table.setItem(row, 3, it_dept)

            it_plan = QTableWidgetItem(plan.title if plan else "-")
            it_plan.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            table.setItem(row, 4, it_plan)

            it_due = QTableWidgetItem(str(s.due_date))
            it_due.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            table.setItem(row, 5, it_due)

            # Status Badge
            badge = StatusBadge(s.status)
            table.setCellWidget(row, 6, badge)

            # Actions Cell
            if s.status in ["scheduled", "overdue"]:
                exec_btn = ActionButton(
                    action_type="execute",
                    tooltip=tr("pm.execute_pm"),
                    text=tr("pm.execute_pm"),
                    callback=lambda _, sid=s.id: self._open_execute_dialog(sid)
                )
                actions_widget = create_actions_cell(exec_btn)
            else:
                view_btn = ActionButton(
                    action_type="view",
                    tooltip=tr("common.details"),
                    text=tr("common.details"),
                    callback=lambda _, sid=s.id: self._view_execution_details(sid)
                )
                actions_widget = create_actions_cell(view_btn)

            table.setCellWidget(row, 7, actions_widget)

        self.schedules_table.set_record_count(len(schedules), len(schedules))

    def _load_plans(self):
        with get_db() as db:
            plans = pm_service.list_pm_plans(db, active_only=False)
            self.all_plans = plans
            self._render_plans(plans)

    def _render_plans(self, plans):
        table = self.plans_table.table
        table.setRowCount(len(plans))

        for row, p in enumerate(plans):
            target = p.category or (f"Asset #{p.equipment_id}" if p.equipment_id else "All")
            checklist_count = len(p.checklist_template or [])

            it_id = QTableWidgetItem(str(p.id))
            it_id.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            table.setItem(row, 0, it_id)

            it_title = QTableWidgetItem(p.title)
            it_title.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            table.setItem(row, 1, it_title)

            it_targ = QTableWidgetItem(target)
            it_targ.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            table.setItem(row, 2, it_targ)

            it_freq = QTableWidgetItem(f"{p.frequency_days} يوم")
            it_freq.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            table.setItem(row, 3, it_freq)

            it_dur = QTableWidgetItem(f"{p.estimated_duration_minutes} دقيقة")
            it_dur.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            table.setItem(row, 4, it_dur)

            it_chk = QTableWidgetItem(f"{checklist_count} عنصر فحص")
            it_chk.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            table.setItem(row, 5, it_chk)

            # Actions
            edit_btn = ActionButton(
                action_type="edit",
                tooltip=tr("common.edit"),
                callback=lambda _, pid=p.id: self._open_edit_plan_dialog(pid)
            )
            del_btn = ActionButton(
                action_type="delete",
                tooltip=tr("common.delete"),
                callback=lambda _, pid=p.id: self._delete_plan(pid)
            )

            actions_widget = create_actions_cell(edit_btn, del_btn)
            table.setCellWidget(row, 6, actions_widget)

        self.plans_table.set_record_count(len(plans), len(plans))

    def _open_new_plan_dialog(self):
        dlg = PMPlanDialog(parent=self)
        if dlg.exec():
            self.refresh_data()

    def _open_edit_plan_dialog(self, plan_id: int):
        dlg = PMPlanDialog(plan_id=plan_id, parent=self)
        if dlg.exec():
            self.refresh_data()

    def _delete_plan(self, plan_id: int):
        if not confirm_action(self, tr("dialog.confirm_title"), "Are you sure you want to delete this PM Plan?"):
            return
        try:
            with get_db() as db:
                pm_service.delete_pm_plan(db, plan_id)
            self.refresh_data()
        except Exception as e:
            QMessageBox.critical(self, tr("common.error"), str(e))

    def _generate_all_schedules(self):
        count = 0
        with get_db() as db:
            plans = pm_service.list_pm_plans(db, active_only=True)
            for p in plans:
                new_s = pm_service.generate_schedules_for_plan(db, p.id)
                count += len(new_s)
        QMessageBox.information(self, tr("common.success"), f"تم توليد {count} مهمة فحص صيانة وقائية جديدة بنجاح.")
        self.refresh_data()

    def _open_execute_dialog(self, schedule_id: int):
        dlg = PMExecutionDialog(schedule_id=schedule_id, parent=self)
        if dlg.exec():
            self.refresh_data()

    def _view_execution_details(self, schedule_id: int):
        with get_db() as db:
            exec_rec = db.query(PMExecution).filter(PMExecution.pm_schedule_id == schedule_id).first()
            if not exec_rec:
                QMessageBox.information(self, tr("common.details"), "لا توجد تفاصيل فحص مسجلة لهذه المهمة بعد.")
                return

            tech_name = exec_rec.technician.full_name if exec_rec.technician else "غير محدد"
            res = "ناجح ومطابق للمعاير" if exec_rec.passed else "غير مطابق / يحتاج متابعة"
            summary_txt = exec_rec.results_summary or "—"
            measurements_txt = str(exec_rec.measurements) if exec_rec.measurements else "—"
            next_date_txt = str(exec_rec.next_due_date) if exec_rec.next_due_date else "—"
            msg = (
                f"تفاصيل محضر الفحص الوقائي والمعايرة\n\n"
                f"تاريخ الفحص والتنفيذ: {exec_rec.execution_date.strftime('%Y-%m-%d %H:%M')}\n"
                f"المهندس / الفني المنفذ: {tech_name}\n"
                f"النتيجة الإجمالية: {res}\n"
                f"ملخص النتائج والملاحظات: {summary_txt}\n"
                f"قراءات القياس والمعايرة: {measurements_txt}\n"
                f"تاريخ الفحص الدوري القادم: {next_date_txt}"
            )
            QMessageBox.information(self, tr("pm.view_execution"), msg)

    def _on_search_schedules(self, query: str):
        query = query.lower().strip()
        if not query:
            self._render_schedules(self.all_schedules)
            return

        filtered = []
        for s in self.all_schedules:
            eq = s.equipment
            plan = s.plan
            combined = f"{s.id} {eq.asset_number if eq else ''} {eq.name_ar or ''} {eq.name_en or ''} {plan.title if plan else ''}".lower()
            if query in combined:
                filtered.append(s)
        self._render_schedules(filtered)

    def _on_search_plans(self, query: str):
        query = query.lower().strip()
        if not query:
            self._render_plans(self.all_plans)
            return

        filtered = [p for p in self.all_plans if query in p.title.lower() or query in (p.category or '').lower()]
        self._render_plans(filtered)

    def retranslate_ui(self):
        self.title_lbl.setText(tr("pm.title"))
        self.sub_lbl.setText(tr("pm.subtitle"))
        self.gen_btn.setText(tr("pm.generate_schedules"))
        self.add_plan_btn.setText(tr("pm.new_plan"))

        self.card_total.set_title(tr("pm.total_schedules"))
        self.card_scheduled.set_title(tr("pm.scheduled_count"))
        self.card_overdue.set_title(tr("pm.overdue_count"))
        self.card_completed.set_title(tr("pm.completed_count"))

        self.tabs.setTabText(0, tr("pm.tab_schedules"))
        self.tabs.setTabText(1, tr("pm.tab_plans"))

        sched_headers = [
            "#",
            tr("equipment.asset_id"),
            tr("equipment.name"),
            tr("departments.title"),
            tr("pm.plan_title"),
            tr("pm.due_date"),
            tr("common.status"),
            tr("common.actions")
        ]
        self.schedules_table.set_headers(sched_headers)

        plan_headers = [
            "#",
            tr("pm.plan_title"),
            tr("pm.target_category"),
            tr("pm.frequency_days"),
            tr("pm.estimated_duration"),
            tr("pm.checklist"),
            tr("common.actions")
        ]
        self.plans_table.set_headers(plan_headers)
        self.refresh_data()
