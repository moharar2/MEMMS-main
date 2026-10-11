"""
Confirmation dialog for critical operations (deletion, transfer, logout).
Uses clean vector iconography, zero emojis, and full bilingual support.
"""
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt
from src.core.i18n import tr
from src.ui.theme.icons import icon


class ConfirmDialog(QDialog):
    def __init__(self, title: str, message: str, is_danger: bool = True, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(440, 190)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(16)

        # Content Layout
        msg_layout = QHBoxLayout()
        msg_layout.setSpacing(16)

        icon_color = "#DC2626" if is_danger else "#0284C7"
        icon_name = "warning" if is_danger else "info"
        icon_label = QLabel()
        icon_label.setPixmap(icon(icon_name, color=icon_color, size=32).pixmap(32, 32))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.text_label = QLabel(message)
        self.text_label.setWordWrap(True)
        self.text_label.setStyleSheet("font-size: 13px; line-height: 1.5; color: #1E293B; font-weight: 500;")

        msg_layout.addWidget(icon_label)
        msg_layout.addWidget(self.text_label, stretch=1)
        layout.addLayout(msg_layout)

        layout.addStretch()

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.addStretch()

        self.cancel_btn = QPushButton(tr("common.cancel"))
        self.cancel_btn.setProperty("variant", "secondary")
        self.cancel_btn.setIcon(icon("cancel", color="#64748B", size=14))
        self.cancel_btn.clicked.connect(self.reject)

        self.confirm_btn = QPushButton(tr("common.confirm"))
        if is_danger:
            self.confirm_btn.setProperty("variant", "danger")
            self.confirm_btn.setIcon(icon("delete", color="#FFFFFF", size=14))
        else:
            self.confirm_btn.setIcon(icon("check", color="#FFFFFF", size=14))
        self.confirm_btn.clicked.connect(self.accept)

        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.confirm_btn)
        layout.addLayout(btn_layout)


def confirm_action(parent, title: str, message: str, is_danger: bool = True) -> bool:
    dialog = ConfirmDialog(title=title, message=message, is_danger=is_danger, parent=parent)
    return dialog.exec() == QDialog.DialogCode.Accepted
