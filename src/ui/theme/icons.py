"""
Central Icon Provider for MEMMS.
Wraps QtAwesome with clean enterprise fallbacks.
Completely replaces emojis with modern vector UI icons.
"""
from typing import Optional
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon, QColor, QPixmap, QPainter
from PySide6.QtCore import QSize, Qt

try:
    import qtawesome as qta
    HAS_QTA = True
except ImportError:
    HAS_QTA = False
    qta = None


class IconHelper:
    """
    Central helper for creating consistent vector icons across the application.
    """
    # Standard icon name mappings (FontAwesome 5 Solid)
    ICONS = {
        # Navigation
        "dashboard": "fa5s.tachometer-alt",
        "equipment": "fa5s.laptop-medical",
        "departments": "fa5s.hospital",
        "locations": "fa5s.map-marker-alt",
        "work_orders": "fa5s.tools",
        "preventive": "fa5s.calendar-check",
        "schedule": "fa5s.clock",
        "inventory": "fa5s.boxes",
        "stock": "fa5s.warehouse",
        "vendors": "fa5s.truck",
        "contracts": "fa5s.file-signature",
        "technicians": "fa5s.user-cog",
        "reports": "fa5s.chart-bar",
        "users": "fa5s.users-cog",
        "audit_logs": "fa5s.clipboard-list",
        "settings": "fa5s.sliders-h",
        "backup": "fa5s.database",

        # Actions
        "search": "fa5s.search",
        "add": "fa5s.plus",
        "edit": "fa5s.pencil-alt",
        "delete": "fa5s.trash-alt",
        "view": "fa5s.eye",
        "transfer": "fa5s.exchange-alt",
        "refresh": "fa5s.sync-alt",
        "filter": "fa5s.filter",
        "clear": "fa5s.times",
        "save": "fa5s.check",
        "cancel": "fa5s.times",
        "close": "fa5s.times",
        "export_excel": "fa5s.file-excel",
        "export_pdf": "fa5s.file-pdf",
        "print": "fa5s.print",
        "logout": "fa5s.sign-out-alt",

        # UI Indicators & States
        "hospital_brand": "fa5s.heartbeat",
        "bell": "fa5s.bell",
        "user": "fa5s.user-circle",
        "globe": "fa5s.globe",
        "moon": "fa5s.moon",
        "sun": "fa5s.sun",
        "check": "fa5s.check-circle",
        "warning": "fa5s.exclamation-triangle",
        "error": "fa5s.times-circle",
        "info": "fa5s.info-circle",
        "question": "fa5s.question-circle",
        "arrow_right": "fa5s.arrow-right",
        "arrow_left": "fa5s.arrow-left",
        "chevron_down": "fa5s.chevron-down",
        "chevron_up": "fa5s.chevron-up",
        "chevron_left": "fa5s.chevron-left",
        "chevron_right": "fa5s.chevron-right",
        "folder": "fa5s.folder",
        "folder_open": "fa5s.folder-open",
        "calendar": "fa5s.calendar-alt",
        "check_double": "fa5s.clipboard-check",
        "history": "fa5s.history",
        "shield": "fa5s.shield-alt",
        "wrench": "fa5s.wrench",
        "stethoscope": "fa5s.stethoscope",
        "dollar": "fa5s.dollar-sign",
        "file_alt": "fa5s.file-alt"
    }

    @classmethod
    def get(cls, name: str, color: Optional[str] = None, size: int = 16) -> QIcon:
        """
        Retrieves a styled QIcon by semantic key safely checking for active QApplication.
        """
        icon_name = cls.ICONS.get(name, name)

        if HAS_QTA and QApplication.instance() is not None:
            try:
                kwargs = {}
                if color:
                    kwargs["color"] = color
                return qta.icon(icon_name, **kwargs)
            except Exception:
                pass

        # Fallback icon if qtawesome fails
        return cls._create_fallback_icon(color or "#0F766E", size)

    @classmethod
    def _create_fallback_icon(cls, color_str: str, size: int) -> QIcon:
        if QApplication.instance() is None:
            return QIcon()

        pix = QPixmap(size, size)
        pix.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(color_str))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(2, 2, size - 4, size - 4)
        painter.end()
        return QIcon(pix)


def icon(name: str, color: Optional[str] = None, size: int = 16) -> QIcon:
    """Convenience function to get a styled icon."""
    return IconHelper.get(name, color=color, size=size)
