"""
pages.py
--------
Placeholder pages for sections that are not implemented in Phase 1.

Every sidebar entry except Dashboard gets its own PlaceholderPage. The
widget is bilingual and re-translates on language switch, so it stays
useful as a real "coming soon" page instead of a dead button.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from .translations import Translator


class PlaceholderPage(QWidget):
    """A bilingual 'Coming in a future phase' page."""

    def __init__(
        self,
        title_key: str,
        translator: Translator,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("PlaceholderPage")
        self._title_key = title_key
        self._translator = translator

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignCenter)

        self.badge = QLabel()
        self.badge.setObjectName("placeholderBadge")
        self.badge.setAlignment(Qt.AlignCenter)

        self.title = QLabel()
        self.title.setObjectName("placeholderTitle")
        self.title.setAlignment(Qt.AlignCenter)

        self.body = QLabel()
        self.body.setObjectName("placeholderBody")
        self.body.setAlignment(Qt.AlignCenter)
        self.body.setWordWrap(True)

        layout.addStretch(1)
        layout.addWidget(self.badge, 0, Qt.AlignHCenter)
        layout.addWidget(self.title, 0, Qt.AlignHCenter)
        layout.addWidget(self.body, 0, Qt.AlignHCenter)
        layout.addStretch(1)

        self.retranslate_ui(self._translator.lang)

    def retranslate_ui(self, lang: str) -> None:
        self.badge.setText(self._translator.t("placeholder.phase"))
        self.title.setText(self._translator.t(self._title_key))
        self.body.setText(self._translator.t("placeholder.body"))
