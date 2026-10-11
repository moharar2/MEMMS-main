"""
Empty state component for tables and views when no records are found.
Crisp vector icons, zero emojis, zero text clipping or overlapping in Arabic RTL.
"""
from typing import Optional, Callable
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFrame
from PySide6.QtCore import Qt
from src.ui.theme.icons import icon


class EmptyStateWidget(QWidget):
    def __init__(
        self,
        title: str,
        description: str,
        action_text: Optional[str] = None,
        action_callback: Optional[Callable] = None,
        icon_name: str = "search",
        parent=None
    ):
        super().__init__(parent)
        self.setMinimumHeight(240)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 36, 24, 36)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(12)

        # Icon container with soft circular tint
        self.icon_badge = QLabel()
        self.icon_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_badge.setFixedSize(64, 64)
        self.icon_badge.setPixmap(icon(icon_name, color="#64748B", size=30).pixmap(30, 30))
        self.icon_badge.setStyleSheet("""
            background-color: #F1F5F9;
            border: 1px solid #E2E8F0;
            border-radius: 32px;
        """)
        layout.addWidget(self.icon_badge, alignment=Qt.AlignmentFlag.AlignCenter)

        # Title
        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("""
            font-size: 16px;
            font-weight: 800;
            color: #1E293B;
            margin-top: 4px;
        """)
        layout.addWidget(self.title_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Description with proper wrapping and clear line spacing
        self.desc_label = QLabel(description)
        self.desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.desc_label.setWordWrap(True)
        self.desc_label.setMinimumWidth(300)
        self.desc_label.setMaximumWidth(520)
        self.desc_label.setStyleSheet("""
            font-size: 13px;
            color: #64748B;
            font-weight: 500;
            line-height: 1.5;
            padding: 0 10px;
        """)
        layout.addWidget(self.desc_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Optional Action Button
        if action_text and action_callback:
            self.action_btn = QPushButton(action_text)
            self.action_btn.setIcon(icon("refresh", color="#475569", size=14))
            self.action_btn.setFixedHeight(38)
            self.action_btn.setMinimumWidth(160)
            self.action_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.action_btn.setStyleSheet("""
                QPushButton {
                    background-color: #F8FAFC;
                    color: #334155;
                    border: 1px solid #CBD5E1;
                    border-radius: 6px;
                    font-size: 13px;
                    font-weight: 700;
                    padding: 6px 18px;
                }
                QPushButton:hover {
                    background-color: #F1F5F9;
                    border-color: #94A3B8;
                    color: #0F172A;
                }
            """)
            self.action_btn.clicked.connect(action_callback)
            layout.addWidget(self.action_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        else:
            self.action_btn = None

    def update_content(self, title: str, description: str, action_text: Optional[str] = None):
        self.title_label.setText(title)
        self.desc_label.setText(description)
        if self.action_btn and action_text:
            self.action_btn.setText(action_text)

