"""
Generic placeholder view for modules planned for upcoming phases.
Zero emojis, clean vector icons, fully localized.
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt
from src.core.i18n import tr
from src.ui.theme.icons import icon


class PlaceholderView(QWidget):
    def __init__(self, title_key: str, icon_name: str = "settings", phase_info: str = "Upcoming Phase", parent=None):
        super().__init__(parent)
        self.title_key = title_key
        self.icon_name = icon_name
        self.phase_info = phase_info

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QFrame()
        card.setProperty("frameShape", "card")
        card.setFixedSize(520, 260)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(32, 32, 32, 32)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.setSpacing(14)

        self.icon_lbl = QLabel()
        self.icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_lbl.setPixmap(icon(self.icon_name, color="#0F766E", size=48).pixmap(48, 48))

        self.title_lbl = QLabel(tr(self.title_key, default=self.title_key))
        self.title_lbl.setStyleSheet("font-size: 18px; font-weight: 800; color: #0F172A;")
        self.title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.desc_lbl = QLabel(tr("placeholder.desc", phase=self.phase_info))
        self.desc_lbl.setStyleSheet("font-size: 13px; color: #64748B; line-height: 1.4;")
        self.desc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card_layout.addWidget(self.icon_lbl)
        card_layout.addWidget(self.title_lbl)
        card_layout.addWidget(self.desc_lbl)

        layout.addWidget(card)

    def retranslate_ui(self):
        self.title_lbl.setText(tr(self.title_key, default=self.title_key))
        self.desc_lbl.setText(tr("placeholder.desc", phase=self.phase_info))
