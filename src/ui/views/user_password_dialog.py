"""
User Password Reset Dialog.
Allows administrators or authorized users to reset credentials for a user account.
Pure Arabic, RTL, zero emojis.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QPushButton, QFrame, QMessageBox
)
from PySide6.QtCore import Qt

from src.core.i18n import tr
from src.core.database import get_db
from src.services.user_service import user_service
from src.services.auth_service import auth_service
from src.ui.theme.icons import icon


class UserPasswordDialog(QDialog):
    def __init__(self, user_id: int, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.setWindowTitle("إعادة تعيين كلمة المرور — نظام إدارة الصيانة الطبية MEMMS")
        self.resize(460, 320)
        self.setFixedSize(460, 320)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(16)

        # Header Frame
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 4)
        header_layout.setSpacing(12)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(icon("settings", color="#0F766E", size=24).pixmap(24, 24))

        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        dlg_title = QLabel("إعادة تعيين كلمة المرور")
        dlg_title.setStyleSheet("font-size: 16px; font-weight: 800; color: #0F172A;")
        self.dlg_sub = QLabel("تعيين كلمة مرور جديدة لحساب المستخدم")
        self.dlg_sub.setStyleSheet("font-size: 12px; color: #64748B;")
        title_layout.addWidget(dlg_title)
        title_layout.addWidget(self.dlg_sub)

        header_layout.addWidget(icon_lbl)
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        main_layout.addWidget(header_frame)

        # Info card
        self.info_card = QLabel("")
        self.info_card.setStyleSheet("""
            background-color: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 6px;
            padding: 8px 12px;
            font-weight: 700;
            color: #0F766E;
            font-size: 12px;
        """)
        main_layout.addWidget(self.info_card)

        # Grid form
        grid = QGridLayout()
        grid.setSpacing(10)

        grid.addWidget(QLabel("كلمة المرور الجديدة *"), 0, 0)
        self.new_pwd_edit = QLineEdit()
        self.new_pwd_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_pwd_edit.setPlaceholderText("6 خانات على الأقل")
        grid.addWidget(self.new_pwd_edit, 0, 1)

        grid.addWidget(QLabel("تأكيد كلمة المرور *"), 1, 0)
        self.confirm_pwd_edit = QLineEdit()
        self.confirm_pwd_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_pwd_edit.setPlaceholderText("أعد كتابة كلمة المرور")
        grid.addWidget(self.confirm_pwd_edit, 1, 1)

        main_layout.addLayout(grid)
        main_layout.addStretch()

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("إلغاء")
        cancel_btn.setIcon(icon("cancel", color="#64748B", size=14))
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("تأكيد التغيير")
        save_btn.setObjectName("primaryBtn")
        save_btn.setIcon(icon("save", color="#FFFFFF", size=14))
        save_btn.clicked.connect(self._on_save)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        main_layout.addLayout(btn_layout)

        self._load_user_info()

    def _load_user_info(self):
        with get_db() as db:
            user = user_service.get_user_by_id(db, self.user_id)
            self.info_card.setText(f"المستخدم: {user.full_name} ({user.username}) • الدور: {user.role.display_name_ar if user.role else '-'}")

    def _on_save(self):
        p1 = self.new_pwd_edit.text()
        p2 = self.confirm_pwd_edit.text()

        if not p1 or len(p1) < 6:
            QMessageBox.warning(self, "تنبيه", "كلمة المرور يجب ألا تقل عن 6 خانات.")
            self.new_pwd_edit.setFocus()
            return

        if p1 != p2:
            QMessageBox.warning(self, "تنبيه", "كلمة المرور وتأكيد كلمة المرور غير متطابقين.")
            self.confirm_pwd_edit.setFocus()
            return

        current_user = auth_service.current_user
        try:
            with get_db() as db:
                user_service.reset_password(
                    db=db,
                    current_user=current_user,
                    user_id=self.user_id,
                    new_password=p1
                )
            QMessageBox.information(self, "نجاح", "تمت إعادة تعيين كلمة المرور بنجاح.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))
