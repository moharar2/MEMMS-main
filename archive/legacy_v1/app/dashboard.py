"""
dashboard.py
------------
The Dashboard page. Shows three statistic cards whose values come from
real database queries, not hard-coded numbers.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from database import get_session
from models import Equipment, Staff, WorkOrder
from .translations import TranslatableWidget, Translator


class StatCard(QFrame, TranslatableWidget):
    """A single statistic card: title + value + small hint line."""

    def __init__(
        self,
        title_key: str,
        translator: Translator,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("StatCard")
        self._title_key = title_key
        self._translator = translator

        # Use a vertical layout. Stretch keeps the value visually centered.
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(6)

        self.title_label = QLabel()
        self.title_label.setObjectName("cardTitle")

        self.value_label = QLabel("—")
        self.value_label.setObjectName("cardValue")
        self.value_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.hint_label = QLabel("")
        self.hint_label.setObjectName("cardHint")

        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addStretch(1)
        layout.addWidget(self.hint_label)

        # Populate the initial label text right away.
        self.retranslate_ui(self._translator.lang)

    def set_value(self, value: int) -> None:
        """Display an integer count. Falls back to '—' on bad input."""
        try:
            self.value_label.setText(str(int(value)))
        except (TypeError, ValueError):
            self.value_label.setText("—")

    def retranslate_ui(self, lang: str) -> None:
        # `lang` is the new language code; we use it to drive the lookup.
        # We do NOT need to keep a Translator reference here, but reusing
        # `self._translator` keeps a single source of truth.
        self.title_label.setText(self._translator.t(self._title_key))


class DashboardPage(QWidget, TranslatableWidget):
    """Container that holds the three StatCards in a horizontal row."""

    def __init__(self, translator: Translator, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._translator = translator

        # Outer layout: vertical so we can add a heading row above cards.
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(20)

        # Heading area.
        self.title_label = QLabel()
        self.title_label.setObjectName("pageTitle")
        self.subtitle_label = QLabel()
        self.subtitle_label.setObjectName("pageSubtitle")
        outer.addWidget(self.title_label)
        outer.addWidget(self.subtitle_label)

        # Cards row.
        cards_row = QHBoxLayout()
        cards_row.setSpacing(16)

        self.card_equipment = StatCard("dashboard.card.equipment", translator)
        self.card_work_orders = StatCard("dashboard.card.work_orders", translator)
        self.card_staff = StatCard("dashboard.card.staff", translator)

        cards_row.addWidget(self.card_equipment)
        cards_row.addWidget(self.card_work_orders)
        cards_row.addWidget(self.card_staff)
        cards_row.addStretch(1)

        outer.addLayout(cards_row)
        outer.addStretch(1)

        # Initial population of labels + values.
        self.retranslate_ui(self._translator.lang)
        self.refresh_stats()

    # ----- Public API ---------------------------------------------------
    def refresh_stats(self) -> None:
        """Run three COUNT queries against SQLite and update the cards."""
        try:
            with get_session() as session:
                total_equipment = session.query(Equipment).count()
                # Phase 1 treats any non-closed work order as "open".
                open_work_orders = (
                    session.query(WorkOrder)
                    .filter(WorkOrder.status != "closed")
                    .count()
                )
                registered_staff = session.query(Staff).count()
        except Exception as exc:  # pragma: no cover - defensive
            # Surface the failure on each card instead of crashing the UI.
            self.card_equipment.value_label.setText("—")
            self.card_work_orders.value_label.setText("—")
            self.card_staff.value_label.setText("—")
            self.subtitle_label.setText(str(exc))
            return

        self.card_equipment.set_value(total_equipment)
        self.card_work_orders.set_value(open_work_orders)
        self.card_staff.set_value(registered_staff)

    # ----- i18n ----------------------------------------------------------
    def retranslate_ui(self, lang: str) -> None:
        self.title_label.setText(self._translator.t("dashboard.title"))
        self.subtitle_label.setText(self._translator.t("dashboard.subtitle"))
