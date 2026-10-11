"""
Enterprise Top Navigation Bar component.
Clean, minimalistic, pure Arabic RTL.
Includes section title, hospital indicator, user profile capsule, and sign-out.
"""
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, Signal
from src.core.i18n import tr
from src.ui.theme.icons import icon
from src.services.auth_service import auth_service
from src.core.database import get_db
from src.models.hospital import Hospital


class TopNavbar(QFrame):
    logout_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(58)
        self.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-bottom: 1px solid #E2E8F0;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(14)

        # 1. Section Title & Hospital Name (Right side in RTL)
        titles_box = QHBoxLayout()
        titles_box.setSpacing(12)

        self.section_title = QLabel("لوحة المؤشرات")
        self.section_title.setStyleSheet("font-size: 16px; font-weight: 800; color: #0F172A;")

        self.hospital_badge = QLabel("المستشفى العام")
        self.hospital_badge.setStyleSheet("""
            font-size: 11px;
            font-weight: 700;
            color: #0F766E;
            background-color: #CCFBF1;
            border-radius: 4px;
            padding: 4px 10px;
        """)

        titles_box.addWidget(self.section_title)
        titles_box.addWidget(self.hospital_badge)
        layout.addLayout(titles_box)

        layout.addStretch()

        # 2. User Profile Capsule (Left side in RTL)
        self.user_capsule = QLabel()
        self._update_user_display()
        self.user_capsule.setStyleSheet("""
            background-color: #F8FAFC;
            color: #1E293B;
            border: 1px solid #CBD5E1;
            border-radius: 16px;
            padding: 5px 14px;
            font-size: 12px;
            font-weight: 700;
        """)
        layout.addWidget(self.user_capsule)

        # 3. Sign Out Button
        self.logout_btn = QPushButton("تسجيل الخروج")
        self.logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.logout_btn.setIcon(icon("logout", color="#DC2626", size=14))
        self.logout_btn.setFixedHeight(34)
        self.logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #FEF2F2;
                color: #DC2626;
                border: 1px solid #FECACA;
                border-radius: 6px;
                font-weight: 700;
                font-size: 12px;
                padding: 4px 14px;
            }
            QPushButton:hover {
                background-color: #FEE2E2;
                border-color: #FCA5A5;
            }
        """)
        self.logout_btn.clicked.connect(self.logout_requested.emit)
        layout.addWidget(self.logout_btn)

        self._load_hospital_name()

    def set_title(self, title: str):
        self.section_title.setText(title)

    def _load_hospital_name(self):
        try:
            with get_db() as db:
                hosp = db.query(Hospital).first()
                if hosp and hosp.name_ar:
                    self.hospital_badge.setText(hosp.name_ar)
        except Exception:
            pass

    def _update_user_display(self):
        user = auth_service.current_user
        if user:
            role_title = "مستخدم"
            is_admin = False
            full_name = ""
            try:
                with get_db() as db:
                    u = db.query(User).filter_by(id=user.id).first()
                    if u:
                        full_name = u.full_name or ""
                        if u.role:
                            role_title = u.role.display_name_ar or u.role.name
                            is_admin = u.role.name == "admin"
            except Exception:
                pass

            clean_name = full_name.replace("System Administrator / ", "").replace(" / System Administrator", "").strip()
            if clean_name == role_title or not clean_name:
                display_text = f"{role_title} (مسؤول)" if is_admin else role_title
            else:
                display_text = f"{clean_name}  •  {role_title}"
            self.user_capsule.setText(display_text)
        else:
            self.user_capsule.setText("مستخدم النظام")

    def retranslate_ui(self):
        self._load_hospital_name()
        self._update_user_display()
        self.logout_btn.setText("تسجيل الخروج")
