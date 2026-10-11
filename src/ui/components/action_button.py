"""
Reusable, high-contrast Table Action Buttons for MEMMS.
Provides standardized, elegant, and crisp action buttons for data tables:
- View / Details
- Edit
- Delete
- Transfer
- Stock Movement / Execution
Ensures buttons never render as compressed, stretched, or illegible solid blocks.
"""
from typing import Callable, Optional
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QSizePolicy
from PySide6.QtCore import Qt
from src.ui.theme.icons import icon


class ActionButton(QPushButton):
    """
    Dedicated action button with explicit styling and zero clipping padding.
    """
    def __init__(
        self,
        action_type: str,
        tooltip: str = "",
        text: Optional[str] = None,
        callback: Optional[Callable] = None,
        parent=None
    ):
        super().__init__(text or "", parent)
        self.action_type = action_type
        self.setProperty("actionButton", "true")
        self.setProperty("actionType", action_type)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        if tooltip:
            self.setToolTip(tooltip)
        if callback:
            self.clicked.connect(callback)

        self._apply_style(action_type, bool(text))

    def _apply_style(self, action_type: str, has_text: bool):
        if not has_text:
            self.setFixedSize(28, 28)
            self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        else:
            self.setFixedHeight(28)
            self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        # Style definitions tailored for enterprise medical UI
        styles = {
            "view": {
                "icon": "view",
                "color": "#0F766E",
                "bg": "#F0FDFA",
                "border": "#CCFBF1",
                "hover_bg": "#CCFBF1",
                "hover_border": "#99F6E4",
                "text_color": "#0F766E"
            },
            "edit": {
                "icon": "edit",
                "color": "#334155",
                "bg": "#F8FAFC",
                "border": "#CBD5E1",
                "hover_bg": "#E2E8F0",
                "hover_border": "#94A3B8",
                "text_color": "#0F172A"
            },
            "delete": {
                "icon": "delete",
                "color": "#DC2626",
                "bg": "#FEF2F2",
                "border": "#FECACA",
                "hover_bg": "#FEE2E2",
                "hover_border": "#FCA5A5",
                "text_color": "#DC2626"
            },
            "transfer": {
                "icon": "transfer",
                "color": "#D97706",
                "bg": "#FFFBEB",
                "border": "#FDE68A",
                "hover_bg": "#FEF3C7",
                "hover_border": "#FCD34D",
                "text_color": "#D97706"
            },
            "stock": {
                "icon": "stock",
                "color": "#0F766E",
                "bg": "#F0FDFA",
                "border": "#99F6E4",
                "hover_bg": "#CCFBF1",
                "hover_border": "#5EEAD4",
                "text_color": "#0F766E"
            },
            "execute": {
                "icon": "check_double",
                "color": "#059669",
                "bg": "#ECFDF5",
                "border": "#A7F3D0",
                "hover_bg": "#D1FAE5",
                "hover_border": "#6EE7B7",
                "text_color": "#059669"
            },
            "history": {
                "icon": "history",
                "color": "#6366F1",
                "bg": "#EEF2FF",
                "border": "#C7D2FE",
                "hover_bg": "#E0E7FF",
                "hover_border": "#A5B4FC",
                "text_color": "#4F46E5"
            },
            "print": {
                "icon": "print",
                "color": "#0284C7",
                "bg": "#F0F9FF",
                "border": "#BAE6FD",
                "hover_bg": "#E0F2FE",
                "hover_border": "#7DD3FC",
                "text_color": "#0284C7"
            }
        }

        conf = styles.get(action_type, styles["edit"])
        self.setIcon(icon(conf["icon"], color=conf["color"], size=13))

        padding_str = "padding: 2px 10px;" if has_text else "padding: 0px;"
        
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {conf['bg']};
                color: {conf['text_color']};
                border: 1px solid {conf['border']};
                border-radius: 6px;
                {padding_str}
                font-size: 11px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background-color: {conf['hover_bg']};
                border-color: {conf['hover_border']};
            }}
            QPushButton:pressed {{
                background-color: {conf['border']};
            }}
        """)


def create_actions_cell(*buttons) -> QWidget:
    """
    Wraps a list of action buttons into a clean, compact centered widget
    ready to be placed into a table cell with setCellWidget.
    Supports both create_actions_cell(b1, b2) and create_actions_cell([b1, b2]).
    """
    container = QWidget()
    container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    container.setStyleSheet("background: transparent;")
    layout = QHBoxLayout(container)
    layout.setContentsMargins(4, 2, 4, 2)
    layout.setSpacing(6)
    layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

    flat_buttons = []
    for b in buttons:
        if isinstance(b, (list, tuple)):
            flat_buttons.extend(b)
        else:
            flat_buttons.append(b)

    for btn in flat_buttons:
        if btn is not None:
            layout.addWidget(btn)

    return container

