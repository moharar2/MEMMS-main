"""
User Add / Edit Dialog.
Enterprise 2-column form for managing user credentials, full name, role, and active status.
Pure Arabic, RTL, zero emojis.
"""
from typing import Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QComboBox, QCheckBox, QPushButton, QFrame, QMessageBox
)
from PySide6.QtCore import Qt

from src.core.i18n import tr
from src.core.database import get_db
from src.models.user import User
from src.models.role import Role
from src.services.user_service import user_service
from src.services.auth_service import auth_service
from src.ui.theme.icons import icon


class UserDialog(QDialog):
    def __init__(self, user_id: Optional[int] = None, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        action_title = tr("users.edit_user") if user_id else tr("users.add_user")
        self.setWindowTitle(f"{action_title} — نظام إدارة الصيانة الطبية MEMMS")
        self.resize(580, 480)
        self.setMinimumSize(520, 420)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(16)

        # 1. Header Frame
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 4)
        header_layout.setSpacing(12)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(icon("users", color="#0F766E", size=26).pixmap(26, 26))

        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        dlg_title = QLabel(action_title)
        dlg_title.setStyleSheet("font-size: 17px; font-weight: 800; color: #0F172A;")
        dlg_sub = QLabel("تحديد الصلاحيات، بيانات الاعتماد، والوظيفة الإدارية أو الفنية")
        dlg_sub.setStyleSheet("font-size: 12px; color: #64748B;")
        title_layout.addWidget(dlg_title)
        title_layout.addWidget(dlg_sub)

        header_layout.addWidget(icon_lbl)
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        main_layout.addWidget(header_frame)

        # 2. Form Grid
        grid = QGridLayout()
        grid.setSpacing(12)

        # Row 0: Username & Full Name
        grid.addWidget(QLabel("اسم المستخدم (Username) *"), 0, 0)
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("مثال: ahmed_engineer")
        grid.addWidget(self.username_edit, 0, 1)

        grid.addWidget(QLabel("الاسم الكامل *"), 0, 2)
        self.fullname_edit = QLineEdit()
        self.fullname_edit.setPlaceholderText("مثال: م. أحمد صالح الصنعاني")
        grid.addWidget(self.fullname_edit, 0, 3)

        # Row 1: Role & Phone
        grid.addWidget(QLabel("الدور الوظيفي والصلاحيات *"), 1, 0)
        self.role_combo = QComboBox()
        grid.addWidget(self.role_combo, 1, 1)

        grid.addWidget(QLabel("رقم الهاتف المباشر"), 1, 2)
        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("مثال: 777123456")
        grid.addWidget(self.phone_edit, 1, 3)

        # Row 2: Email
        grid.addWidget(QLabel("البريد الإلكتروني"), 2, 0)
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("example@hospital.ye")
        grid.addWidget(self.email_edit, 2, 1, 1, 3)

        # Row 3 & 4: Password fields (Create mode only)
        if not self.user_id:
            grid.addWidget(QLabel("كلمة المرور *"), 3, 0)
            self.password_edit = QLineEdit()
            self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
            self.password_edit.setPlaceholderText("6 خانات على الأقل")
            grid.addWidget(self.password_edit, 3, 1)

            grid.addWidget(QLabel("تأكيد كلمة المرور *"), 3, 2)
            self.confirm_password_edit = QLineEdit()
            self.confirm_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
            self.confirm_password_edit.setPlaceholderText("أعد إدخال كلمة المرور")
            grid.addWidget(self.confirm_password_edit, 3, 3)

        # Row 5: Account Status Checkbox
        self.active_check = QCheckBox("حساب نشط ومفعل (يمكنه تسجيل الدخول واستخدام النظام)")
        self.active_check.setChecked(True)
        self.active_check.setStyleSheet("font-weight: 700; color: #0F766E; font-size: 12.5px; padding-top: 6px;")
        grid.addWidget(self.active_check, 4 if not self.user_id else 3, 0, 1, 4)

        main_layout.addLayout(grid)

        # Role Description Box
        self.role_desc_lbl = QLabel("")
        self.role_desc_lbl.setStyleSheet("""
            background-color: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 6px;
            padding: 8px 12px;
            color: #475569;
            font-size: 11.5px;
        """)
        self.role_desc_lbl.setWordWrap(True)
        main_layout.addWidget(self.role_desc_lbl)

        main_layout.addStretch()

        # 3. Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("إلغاء")
        cancel_btn.setIcon(icon("cancel", color="#64748B", size=14))
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("حفظ المستخدم")
        save_btn.setObjectName("primaryBtn")
        save_btn.setIcon(icon("save", color="#FFFFFF", size=14))
        save_btn.clicked.connect(self._on_save)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        main_layout.addLayout(btn_layout)

        self._load_roles()
        self.role_combo.currentIndexChanged.connect(self._update_role_description)
        self._update_role_description()

        if self.user_id:
            self._load_user_data()

    def _load_roles(self):
        with get_db() as db:
            roles = user_service.list_roles(db)
            self.role_descriptions = {}
            for r in roles:
                self.role_combo.addItem(r.display_name_ar, r.id)
                self.role_descriptions[r.id] = r.description or ""

    def _update_role_description(self):
        role_id = self.role_combo.currentData()
        desc = self.role_descriptions.get(role_id, "")
        self.role_desc_lbl.setText(f"نطاق صلاحيات الدور: {desc}" if desc else "")

    def _load_user_data(self):
        with get_db() as db:
            user = user_service.get_user_by_id(db, self.user_id)
            self.username_edit.setText(user.username)
            self.username_edit.setReadOnly(True)
            self.username_edit.setStyleSheet("background-color: #F1F5F9; color: #64748B;")
            self.fullname_edit.setText(user.full_name)
            self.email_edit.setText(user.email or "")
            self.phone_edit.setText(user.phone or "")
            self.active_check.setChecked(user.is_active)

            idx = self.role_combo.findData(user.role_id)
            if idx >= 0:
                self.role_combo.setCurrentIndex(idx)

    def _on_save(self):
        username = self.username_edit.text().strip()
        full_name = self.fullname_edit.text().strip()
        role_id = self.role_combo.currentData()
        email = self.email_edit.text().strip()
        phone = self.phone_edit.text().strip()
        is_active = self.active_check.isChecked()

        if not username:
            QMessageBox.warning(self, "تنبيه", "يرجى إدخال اسم المستخدم.")
            self.username_edit.setFocus()
            return

        if not full_name:
            QMessageBox.warning(self, "تنبيه", "يرجى إدخال الاسم الكامل للمستخدم.")
            self.fullname_edit.setFocus()
            return

        if not role_id:
            QMessageBox.warning(self, "تنبيه", "يرجى اختيار الدور الوظيفي.")
            return

        current_user = auth_service.current_user

        try:
            with get_db() as db:
                if self.user_id:
                    # Update mode
                    user_service.update_user(
                        db=db,
                        current_user=current_user,
                        user_id=self.user_id,
                        user_data={
                            "username": username,
                            "full_name": full_name,
                            "role_id": role_id,
                            "email": email,
                            "phone": phone,
                            "is_active": is_active
                        }
                    )
                else:
                    # Create mode
                    pwd = self.password_edit.text()
                    confirm_pwd = self.confirm_password_edit.text()

                    if not pwd or len(pwd) < 6:
                        QMessageBox.warning(self, "تنبيه", "كلمة المرور يجب ألا تقل عن 6 خانات.")
                        self.password_edit.setFocus()
                        return

                    if pwd != confirm_pwd:
                        QMessageBox.warning(self, "تنبيه", "كلمة المرور وتأكيد كلمة المرور غير متطابقين.")
                        self.confirm_password_edit.setFocus()
                        return

                    user_service.create_user(
                        db=db,
                        current_user=current_user,
                        user_data={
                            "username": username,
                            "full_name": full_name,
                            "role_id": role_id,
                            "password": pwd,
                            "email": email,
                            "phone": phone,
                            "is_active": is_active
                        }
                    )

            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))
