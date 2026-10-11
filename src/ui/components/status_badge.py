"""
StatusBadge component for displaying colored status and priority pills in tables and forms.
Zero emojis, clean rounded borders and high-contrast typography.
"""
from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt
from src.core.i18n import tr


class StatusBadge(QLabel):
    STATUS_STYLES = {
        # Operational Statuses
        "operational": ("#065F46", "#D1FAE5", "#A7F3D0"),   # Dark Green text, Light Green bg
        "active": ("#065F46", "#D1FAE5", "#A7F3D0"),
        "passed": ("#065F46", "#D1FAE5", "#A7F3D0"),
        "completed": ("#065F46", "#D1FAE5", "#A7F3D0"),
        "closed": ("#334155", "#F1F5F9", "#CBD5E1"),        # Slate

        "under_maintenance": ("#92400E", "#FEF3C7", "#FDE68A"), # Amber
        "in_progress": ("#075985", "#E0F2FE", "#BAE6FD"),       # Sky
        "assigned": ("#5B21B6", "#EDE9FE", "#DDD6FE"),          # Violet
        "waiting_parts": ("#9A3412", "#FFEDD5", "#FED7AA"),     # Orange
        "pending": ("#374151", "#F3F4F6", "#E5E7EB"),           # Gray
        "scheduled": ("#075985", "#E0F2FE", "#BAE6FD"),

        "out_of_service": ("#991B1B", "#FEE2E2", "#FECACA"),    # Red
        "failed": ("#991B1B", "#FEE2E2", "#FECACA"),
        "scrapped": ("#334155", "#E2E8F0", "#CBD5E1"),
        "standby": ("#155E75", "#CFFAFE", "#A5F3FC"),           # Cyan
        "overdue": ("#991B1B", "#FEE2E2", "#FECACA"),
        "cancelled": ("#4B5563", "#F3F4F6", "#D1D5DB"),
        "expired": ("#991B1B", "#FEE2E2", "#FECACA"),
        "expiring_soon": ("#92400E", "#FEF3C7", "#FDE68A"),

        # Priorities
        "critical": ("#991B1B", "#FEE2E2", "#FECACA"),
        "high": ("#C2410C", "#FFEDD5", "#FED7AA"),
        "medium": ("#075985", "#E0F2FE", "#BAE6FD"),
        "low": ("#065F46", "#D1FAE5", "#A7F3D0"),

        # Risk Levels
        "risk_high": ("#991B1B", "#FEE2E2", "#FECACA"),
        "risk_medium": ("#075985", "#E0F2FE", "#BAE6FD"),
        "risk_low": ("#065F46", "#D1FAE5", "#A7F3D0"),

        # Criticality
        "semi_critical": ("#075985", "#E0F2FE", "#BAE6FD"),
        "non_critical": ("#065F46", "#D1FAE5", "#A7F3D0")
    }

    ARABIC_FALLBACKS = {
        "operational": "يعمل بكفاءة",
        "active": "نشط",
        "passed": "ناجح",
        "completed": "مكتمل",
        "closed": "مغلق",
        "under_maintenance": "تحت الصيانة",
        "in_progress": "قيد التنفيذ",
        "assigned": "تم التكليف",
        "waiting_parts": "بانتظار قطع الغيار",
        "pending": "قيد الانتظار",
        "scheduled": "مجدول",
        "out_of_service": "خارج الخدمة",
        "failed": "راسب",
        "scrapped": "مكهن",
        "standby": "احتياطي / جاهز",
        "overdue": "متأخر",
        "cancelled": "ملغى",
        "expired": "منتهي",
        "expiring_soon": "ينتهي قريباً",
        "critical": "حرج / طارئ",
        "high": "مرتفع",
        "medium": "متوسط",
        "low": "منخفض",
        "risk_high": "عالي الخطورة",
        "risk_medium": "متوسط الخطورة",
        "risk_low": "منخفض الخطورة",
        "semi_critical": "شبه حرج",
        "non_critical": "غير حرج"
    }

    def __init__(self, status_key: str, parent=None):
        super().__init__(parent)
        self.status_key = status_key
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.update_status(status_key)

    def update_status(self, status_key: str):
        self.status_key = status_key
        key = (status_key or "").lower().strip()
        fg_color, bg_color, border_color = self.STATUS_STYLES.get(
            key, ("#374151", "#F3F4F6", "#E5E7EB")
        )

        display_text = None

        # 1. Direct fallback dictionary hit
        if key in self.ARABIC_FALLBACKS:
            display_text = self.ARABIC_FALLBACKS[key]

        # 2. Risk prefix special lookup
        if not display_text and key.startswith("risk_"):
            stripped = key.replace("risk_", "")
            res = tr(f"risk.{stripped}", default=None)
            if res:
                display_text = res
            elif stripped in self.ARABIC_FALLBACKS:
                display_text = self.ARABIC_FALLBACKS[stripped]

        # 3. Lookup standard translation namespaces
        if not display_text:
            for prefix in ("risk", "status", "priority", "criticality"):
                res = tr(f"{prefix}.{key}", default=None)
                if res:
                    display_text = res
                    break

        # 4. Final fallback
        if not display_text:
            display_text = self.ARABIC_FALLBACKS.get(key, self.ARABIC_FALLBACKS.get(key.replace("risk_", ""), key))

        self.setText(display_text)
        self.setStyleSheet(f"""
            QLabel {{
                color: {fg_color};
                background-color: {bg_color};
                border: 1px solid {border_color};
                font-size: 11px;
                font-weight: 700;
                border-radius: 10px;
                padding: 3px 8px;
                letter-spacing: 0.2px;
            }}
        """)

