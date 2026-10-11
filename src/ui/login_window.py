"""
Enterprise Login Window for MEMMS.
Ultra-clean, high-contrast, pure Arabic medical aesthetic.
Zero emojis, pure white inputs, high-legibility typography.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from src.core.i18n import tr
from src.core.database import get_db
from src.services.auth_service import auth_service
from src.models.user import User
from src.ui.theme.icons import icon


class LoginWindow(QDialog):
    login_successful = Signal(User)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("LoginDialog")
        self.setWindowTitle("تسجيل الدخول — نظام إدارة الصيانة الطبية MEMMS")
        self.setFixedSize(480, 540)
        self.setStyleSheet("""
            QDialog#LoginDialog {
                background-color: #F1F5F9;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 32, 32, 32)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Card Container
        card = QFrame()
        card.setObjectName("LoginCard")
        card.setStyleSheet("""
            QFrame#LoginCard {
                background-color: #FFFFFF;
                border-radius: 12px;
                border: 1px solid #E2E8F0;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(32, 32, 32, 32)
        card_layout.setSpacing(14)

        # Brand Icon & Title
        brand_icon_lbl = QLabel()
        brand_icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand_icon_lbl.setPixmap(icon("hospital_brand", color="#0F766E", size=38).pixmap(38, 38))
        card_layout.addWidget(brand_icon_lbl)

        self.title_lbl = QLabel("MEMMS")
        self.title_lbl.setStyleSheet("font-size: 24px; font-weight: 800; color: #0F766E; letter-spacing: 1px;")
        self.title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.subtitle_lbl = QLabel("نظام إدارة صيانة الأجهزة الطبية")
        self.subtitle_lbl.setStyleSheet("font-size: 13px; color: #475569; font-weight: 600;")
        self.subtitle_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card_layout.addWidget(self.title_lbl)
        card_layout.addWidget(self.subtitle_lbl)

        # Error display banner
        self.error_lbl = QLabel("")
        self.error_lbl.setStyleSheet("""
            color: #DC2626;
            background-color: #FEF2F2;
            border: 1px solid #FECACA;
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 12px;
            font-weight: 600;
        """)
        self.error_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_lbl.setVisible(False)
        card_layout.addWidget(self.error_lbl)

        # Username Input
        self.u_lbl = QLabel("اسم المستخدم")
        self.u_lbl.setStyleSheet("font-size: 12px; font-weight: 700; color: #334155;")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("أدخل اسم المستخدم (مثال: admin)")
        self.username_input.setText("admin")
        self.username_input.setFixedHeight(40)
        self.username_input.setStyleSheet("""
            QLineEdit {
                background-color: #FFFFFF;
                color: #0F172A;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1.5px solid #0F766E;
                background-color: #FFFFFF;
            }
        """)

        # Password Input
        self.p_lbl = QLabel("كلمة المرور")
        self.p_lbl.setStyleSheet("font-size: 12px; font-weight: 700; color: #334155;")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("••••••••")
        self.password_input.setText("Admin@123456")
        self.password_input.setFixedHeight(40)
        self.password_input.setStyleSheet("""
            QLineEdit {
                background-color: #FFFFFF;
                color: #0F172A;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1.5px solid #0F766E;
                background-color: #FFFFFF;
            }
        """)
        self.password_input.returnPressed.connect(self._do_login)

        card_layout.addWidget(self.u_lbl)
        card_layout.addWidget(self.username_input)
        card_layout.addWidget(self.p_lbl)
        card_layout.addWidget(self.password_input)

        # Sign In Button
        self.login_btn = QPushButton("تسجيل الدخول")
        self.login_btn.setFixedHeight(44)
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #0F766E;
                color: #FFFFFF;
                font-size: 14px;
                font-weight: 700;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #0D9488;
            }
            QPushButton:pressed {
                background-color: #115E59;
            }
        """)
        self.login_btn.setIcon(icon("shield", color="#FFFFFF", size=15))
        self.login_btn.clicked.connect(self._do_login)
        card_layout.addWidget(self.login_btn)

        # Credentials Hint
        self.hint_lbl = QLabel("الحساب الافتراضي: admin / Admin@123456")
        self.hint_lbl.setStyleSheet("""
            font-size: 11px;
            color: #64748B;
            background-color: #F8FAFC;
            border: 1px dashed #CBD5E1;
            border-radius: 6px;
            padding: 6px 10px;
            margin-top: 4px;
        """)
        self.hint_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.hint_lbl)

        main_layout.addWidget(card)

    def retranslate_ui(self):
        self.setWindowTitle("تسجيل الدخول — نظام إدارة الصيانة الطبية MEMMS")
        self.subtitle_lbl.setText("نظام إدارة صيانة الأجهزة الطبية")
        self.u_lbl.setText("اسم المستخدم")
        self.p_lbl.setText("كلمة المرور")
        self.login_btn.setText("تسجيل الدخول")

    def _do_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()

        self.error_lbl.setVisible(False)
        try:
            with get_db() as db:
                user = auth_service.authenticate(db, username, password)
                self.login_successful.emit(user)
                self.accept()
        except Exception as e:
            self.error_lbl.setText(str(e))
            self.error_lbl.setVisible(True)
