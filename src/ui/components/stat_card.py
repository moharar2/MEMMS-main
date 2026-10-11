"""
StatCard widget for displaying KPI metrics with vector icons and modern enterprise styling.
Zero emojis, high contrast typography, medical color accents.
"""
from typing import Optional
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QHBoxLayout
from PySide6.QtCore import Qt
from src.ui.theme.icons import icon


class StatCard(QFrame):
    def __init__(
        self,
        title: str,
        value: str,
        icon_name: str = "dashboard",
        accent_color: str = "#0F766E",
        subtitle: Optional[str] = None,
        parent=None
    ):
        super().__init__(parent)
        self.accent_color = accent_color
        self.icon_name = icon_name

        self.setFixedHeight(72)
        self.setStyleSheet(f"""
            StatCard {{
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
            }}
            StatCard:hover {{
                border-color: {accent_color};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # Icon Box
        self.icon_container = QLabel()
        self.icon_container.setFixedSize(36, 36)
        self.icon_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_container.setPixmap(icon(self.icon_name, color=self.accent_color, size=18).pixmap(18, 18))
        self.icon_container.setStyleSheet(f"""
            background-color: {self.accent_color}14;
            border-radius: 6px;
            border: 1px solid {self.accent_color}25;
        """)
        layout.addWidget(self.icon_container)

        # Texts (Title & Value)
        text_layout = QVBoxLayout()
        text_layout.setSpacing(1)
        text_layout.setContentsMargins(0, 0, 0, 0)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748B;")
        text_layout.addWidget(self.title_label)

        val_box = QHBoxLayout()
        val_box.setSpacing(6)
        val_box.setContentsMargins(0, 0, 0, 0)

        self.value_label = QLabel(str(value))
        self.value_label.setStyleSheet("font-size: 18px; font-weight: 800; color: #0F172A;")
        val_box.addWidget(self.value_label)

        if subtitle:
            self.sub_label = QLabel(subtitle)
            self.sub_label.setStyleSheet("font-size: 10px; color: #94A3B8; font-weight: 600;")
            val_box.addWidget(self.sub_label)
        else:
            self.sub_label = None

        val_box.addStretch()
        text_layout.addLayout(val_box)
        layout.addLayout(text_layout)
        layout.addStretch()

    def set_value(self, value: any):
        self.value_label.setText(str(value))

    def set_title(self, title: str):
        self.title_label.setText(title)

    def set_subtitle(self, subtitle: str):
        if self.sub_label:
            self.sub_label.setText(subtitle)


