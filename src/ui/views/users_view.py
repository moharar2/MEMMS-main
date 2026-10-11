"""
Enterprise User Management View.
Pure Arabic RTL, real-time KPI aggregations, role filtering, status toggling, and password management.
Zero emojis, vector UI action buttons.
"""
from typing import Optional, List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QTableWidgetItem, QMessageBox, QFrame
)
from PySide6.QtCore import Qt, QTimer

from src.core.i18n import tr
from src.core.database import get_db
from src.models.user import User
from src.models.role import Role
from src.services.user_service import user_service
from src.services.auth_service import auth_service
from src.ui.theme.icons import icon
from src.ui.components.stat_card import StatCard
from src.ui.components.status_badge import StatusBadge
from src.ui.components.data_table import DataTable
from src.ui.components.action_button import ActionButton, create_actions_cell
from src.ui.views.user_dialog import UserDialog
from src.ui.views.user_password_dialog import UserPasswordDialog


class UsersView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.all_users: List[User] = []
        self._setup_ui()
        QTimer.singleShot(0, self.refresh_data)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 14, 18, 14)
        main_layout.setSpacing(10)

        # 1. Header Section
        header_layout = QHBoxLayout()
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)

        self.title_lbl = QLabel(tr("users.title"))
        self.title_lbl.setStyleSheet("font-size: 18px; font-weight: 800; color: #0F172A;")
        self.sub_lbl = QLabel(tr("users.subtitle"))
        self.sub_lbl.setStyleSheet("font-size: 12px; color: #64748B;")
        title_layout.addWidget(self.title_lbl)
        title_layout.addWidget(self.sub_lbl)
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        # 2. KPI Stat Cards Row
        stat_layout = QHBoxLayout()
        stat_layout.setSpacing(10)

        self.stat_total = StatCard(title=tr("users.total_users"), value="0", icon_name="users", accent_color="#0F766E")
        self.stat_active = StatCard(title=tr("users.active_users"), value="0", icon_name="check", accent_color="#059669")
        self.stat_admins = StatCard(title=tr("users.admin_users"), value="0", icon_name="shield", accent_color="#D97706")
        self.stat_tech = StatCard(title=tr("users.tech_users"), value="0", icon_name="technicians", accent_color="#2563EB")

        stat_layout.addWidget(self.stat_total)
        stat_layout.addWidget(self.stat_active)
        stat_layout.addWidget(self.stat_admins)
        stat_layout.addWidget(self.stat_tech)
        main_layout.addLayout(stat_layout)

        # 3. Filter Bar
        filter_card = QFrame()
        filter_card.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                padding: 4px 8px;
            }
        """)
        filter_layout = QHBoxLayout(filter_card)
        filter_layout.setContentsMargins(8, 4, 8, 4)
        filter_layout.setSpacing(10)

        filter_lbl = QLabel(tr("common.filter") + ":")
        filter_lbl.setStyleSheet("font-weight: 700; color: #475569; font-size: 11px;")
        filter_layout.addWidget(filter_lbl)

        self.role_filter = QComboBox()
        self.role_filter.currentIndexChanged.connect(self.load_data)
        filter_layout.addWidget(self.role_filter)

        self.status_filter = QComboBox()
        self.status_filter.addItem(tr("users.filter_all_statuses"), None)
        self.status_filter.addItem(tr("users.status_active"), True)
        self.status_filter.addItem(tr("users.status_inactive"), False)
        self.status_filter.currentIndexChanged.connect(self.load_data)
        filter_layout.addWidget(self.status_filter)

        filter_layout.addStretch()

        self.reset_filter_btn = QPushButton(tr("common.clear_filter"))
        self.reset_filter_btn.setProperty("variant", "secondary")
        self.reset_filter_btn.setIcon(icon("clear", color="#64748B", size=12))
        self.reset_filter_btn.clicked.connect(self._reset_filters)
        filter_layout.addWidget(self.reset_filter_btn)

        main_layout.addWidget(filter_card)

        # 4. Data Table
        self.header_keys = [
            "#",
            "users.username",
            "users.full_name",
            "users.role",
            "users.phone",
            "users.status",
            "common.actions"
        ]
        headers = [
            "#",
            tr("users.username"),
            tr("users.full_name"),
            tr("users.role"),
            "رقم الهاتف / البريد",
            tr("users.status"),
            tr("common.actions")
        ]

        self.table_widget = DataTable()
        self.table_widget.set_headers(headers, self.header_keys)
        # 0: ID, 1: Username, 2: FullName, 3: Role, 4: Contact, 5: Status, 6: Actions
        self.table_widget.set_column_widths([45, 120, 180, 140, 160, 95, 120], stretch_cols=[2, 4])
        self.table_widget.table.verticalHeader().setDefaultSectionSize(38)

        self.table_widget.set_add_button_text("+ " + tr("users.add_user"))
        self.table_widget.set_add_button_visible(True)
        self.table_widget.search_changed.connect(lambda txt: self.load_data())
        self.table_widget.refresh_requested.connect(self.refresh_data)
        self.table_widget.add_requested.connect(self._on_add_user)
        self.table_widget.table.cellDoubleClicked.connect(self._on_row_double_clicked)
        main_layout.addWidget(self.table_widget, stretch=1)

        self._populate_role_filter()

    def _populate_role_filter(self):
        self.role_filter.clear()
        self.role_filter.addItem(tr("users.filter_all_roles"), None)
        with get_db() as db:
            roles = user_service.list_roles(db)
            for r in roles:
                self.role_filter.addItem(r.display_name_ar, r.id)

    def _reset_filters(self):
        self.role_filter.setCurrentIndex(0)
        self.status_filter.setCurrentIndex(0)
        self.table_widget.search_input.clear()
        self.load_data()

    def refresh_data(self):
        self._populate_role_filter()
        self.load_data()

    def load_data(self):
        search_txt = self.table_widget.search_input.text().strip()
        role_id = self.role_filter.currentData()
        is_active = self.status_filter.currentData()

        with get_db() as db:
            stats = user_service.get_user_stats(db)
            self.stat_total.set_value(stats["total"])
            self.stat_active.set_value(stats["active"])
            self.stat_admins.set_value(stats["admins"])
            self.stat_tech.set_value(stats["technical"])

            users = user_service.list_users(
                db=db,
                search_query=search_txt or None,
                role_id=role_id,
                is_active=is_active
            )
            self.all_users = users

            tbl = self.table_widget.table
            tbl.setRowCount(len(users))

            for row_idx, u in enumerate(users):
                # 0: ID
                it_id = QTableWidgetItem(str(u.id))
                it_id.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                tbl.setItem(row_idx, 0, it_id)

                # 1: Username
                it_user = QTableWidgetItem(u.username)
                it_user.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                tbl.setItem(row_idx, 1, it_user)

                # 2: Full Name
                it_name = QTableWidgetItem(u.full_name)
                it_name.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                tbl.setItem(row_idx, 2, it_name)

                # 3: Role Badge
                role_name_ar = u.role.display_name_ar if u.role else "-"
                it_role = QTableWidgetItem(role_name_ar)
                it_role.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                tbl.setItem(row_idx, 3, it_role)

                # 4: Contact
                contact_info = u.phone or u.email or "—"
                if u.phone and u.email:
                    contact_info = f"{u.phone} • {u.email}"
                it_contact = QTableWidgetItem(contact_info)
                it_contact.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                tbl.setItem(row_idx, 4, it_contact)

                # 5: Status Badge
                badge = StatusBadge("active" if u.is_active else "inactive")
                tbl.setCellWidget(row_idx, 5, badge)

                # 6: Action Buttons (Edit, Reset Password, Toggle Status)
                edit_btn = ActionButton(
                    action_type="edit",
                    tooltip=tr("users.edit_user"),
                    callback=lambda _, uid=u.id: self._on_edit_user(uid)
                )

                pwd_btn = ActionButton(
                    action_type="settings",
                    tooltip=tr("users.reset_password"),
                    callback=lambda _, uid=u.id: self._on_reset_password(uid)
                )

                toggle_tooltip = "تعطيل الحساب" if u.is_active else "تنشيط الحساب"
                toggle_type = "delete" if u.is_active else "save"
                toggle_btn = ActionButton(
                    action_type=toggle_type,
                    tooltip=toggle_tooltip,
                    callback=lambda _, uid=u.id, cur_state=u.is_active: self._on_toggle_status(uid, not cur_state)
                )

                actions_cell = create_actions_cell(edit_btn, pwd_btn, toggle_btn)
                tbl.setCellWidget(row_idx, 6, actions_cell)

            self.table_widget.set_record_count(len(users), len(users))

    def _on_add_user(self):
        dlg = UserDialog(user_id=None, parent=self)
        if dlg.exec():
            self.load_data()

    def _on_edit_user(self, user_id: int):
        dlg = UserDialog(user_id=user_id, parent=self)
        if dlg.exec():
            self.load_data()

    def _on_reset_password(self, user_id: int):
        dlg = UserPasswordDialog(user_id=user_id, parent=self)
        dlg.exec()

    def _on_toggle_status(self, user_id: int, new_state: bool):
        action_name = "تنشيط" if new_state else "تعطيل"
        confirm = QMessageBox.question(
            self,
            "تأكيد الإجراء",
            f"هل أنت متأكد من رغبتك في {action_name} هذا الحساب؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        current_user = auth_service.current_user
        try:
            with get_db() as db:
                user_service.toggle_user_status(
                    db=db,
                    current_user=current_user,
                    user_id=user_id,
                    is_active=new_state
                )
            self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))

    def _on_row_double_clicked(self, row: int, column: int):
        if row < len(self.all_users):
            u = self.all_users[row]
            self._on_edit_user(u.id)

    def retranslate_ui(self):
        self.title_lbl.setText(tr("users.title"))
        self.sub_lbl.setText(tr("users.subtitle"))
        self.refresh_data()
