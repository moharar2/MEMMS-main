"""
DataTable component with integrated search, filter layout, vector icon buttons,
and integrated empty state indicator. Zero emojis.
Supports both constructor-time headers and deferred set_headers() call.
"""
from typing import List, Optional, Union
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QLineEdit, QPushButton, QLabel, QHeaderView, QAbstractItemView, QStackedWidget
)
from PySide6.QtCore import Qt, Signal, QEvent
from src.core.i18n import tr
from src.ui.theme.icons import icon
from src.ui.components.empty_state import EmptyStateWidget


class ResponsiveTableWidget(QTableWidget):
    """QTableWidget subclass that notifies its parent on resize for dynamic column adjustment."""
    def __init__(self, parent_data_table: "DataTable" = None):
        super().__init__()
        self._parent_data_table = parent_data_table
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

    def setItem(self, row: int, column: int, item: QTableWidgetItem):
        if item is not None:
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        super().setItem(row, column, item)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._parent_data_table:
            self._parent_data_table.adjust_column_widths()


class DataTable(QWidget):
    search_changed = Signal(str)
    add_requested = Signal()
    add_clicked = add_requested
    refresh_requested = Signal()

    def __init__(self, headers: Optional[List[str]] = None, header_keys: Optional[List[str]] = None, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.headers = headers or []
        self.header_keys = header_keys or []
        self._min_widths: List[int] = []
        self._stretch_cols: List[int] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Top Control Bar
        self.top_bar = QHBoxLayout()
        self.top_bar.setContentsMargins(0, 0, 0, 0)
        self.top_bar.setSpacing(10)

        # Search Input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(tr("common.search_placeholder"))
        self.search_input.addAction(icon("search", color="#94A3B8", size=14), QLineEdit.ActionPosition.LeadingPosition)
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self.search_changed.emit)
        self.search_input.setFixedWidth(280)
        self.top_bar.addWidget(self.search_input)

        self.top_bar.addStretch()

        # Action Buttons
        self.refresh_btn = QPushButton(tr("common.refresh"))
        self.refresh_btn.setProperty("variant", "secondary")
        self.refresh_btn.setIcon(icon("refresh", color="#64748B", size=13))
        self.refresh_btn.clicked.connect(self.refresh_requested.emit)
        self.top_bar.addWidget(self.refresh_btn)

        self.add_btn = QPushButton(tr("common.add"))
        self.add_btn.setIcon(icon("add", color="#FFFFFF", size=13))
        self.add_btn.setStyleSheet("""
            QPushButton {
                background-color: #0F766E;
                color: #FFFFFF;
                font-weight: 700;
                padding: 7px 14px;
                border-radius: 6px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #0D9488;
            }
        """)
        self.add_btn.clicked.connect(self.add_requested.emit)
        self.add_btn.setVisible(True)
        self.top_bar.addWidget(self.add_btn)

        layout.addLayout(self.top_bar)

        # Stacked Widget for Table vs Empty State
        self.content_stack = QStackedWidget()

        # Main Table Widget with Responsive resizing
        self.table = ResponsiveTableWidget(self)
        self.table.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.table.setColumnCount(len(self.headers))
        if self.headers:
            self.table.setHorizontalHeaderLabels(self.headers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(38)
        
        # Horizontal header configuration
        header = self.table.horizontalHeader()
        header.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        header.setHighlightSections(False)
        header.setMinimumSectionSize(50)
        header.setStretchLastSection(False)
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)

        # Scrollbar and view settings
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)

        self.content_stack.addWidget(self.table)

        # Empty State
        self.empty_state = EmptyStateWidget(
            title=tr("common.no_data"),
            description=tr("empty_state.no_equipment_desc"),
            action_text=tr("common.refresh"),
            action_callback=self.refresh_requested.emit,
            icon_name="search"
        )
        self.content_stack.addWidget(self.empty_state)

        layout.addWidget(self.content_stack, stretch=1)

        # Bottom Info Bar
        self.info_label = QLabel(tr("common.loading"))
        self.info_label.setStyleSheet("color: #64748B; font-size: 12px; font-weight: 500; padding: 4px;")
        layout.addWidget(self.info_label)

    # ── Public API ─────────────────────────────────────────────────────────────

    def set_headers(self, headers: List[str], header_keys: Optional[List[str]] = None):
        """Update table column headers."""
        self.headers = headers
        if header_keys:
            self.header_keys = header_keys
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.adjust_column_widths()

    def set_column_widths(self, min_widths: List[int], stretch_cols: Optional[List[int]] = None):
        """
        Configure responsive minimum column widths and stretchable columns.
        Guarantees that columns will never shrink below min_widths, while
        distributing extra viewport space across stretch_cols on wide screens.
        """
        self._min_widths = list(min_widths)
        self._stretch_cols = list(stretch_cols or [])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.adjust_column_widths()

    def adjust_column_widths(self):
        """Recalculate and apply column widths based on current viewport size."""
        if not self._min_widths:
            return

        col_count = self.table.columnCount()
        if col_count == 0:
            return

        # Viewport width minus safety margin for borders / scrollbar
        viewport_w = self.table.viewport().width()
        total_min_w = sum(self._min_widths[:col_count])

        if viewport_w > total_min_w and self._stretch_cols:
            extra_pixels = viewport_w - total_min_w
            valid_stretch = [c for c in self._stretch_cols if c < col_count]
            if valid_stretch:
                per_col_add = extra_pixels // len(valid_stretch)
                remainder = extra_pixels % len(valid_stretch)

                for c in range(col_count):
                    w = self._min_widths[c] if c < len(self._min_widths) else 100
                    if c in valid_stretch:
                        bonus = per_col_add + (1 if valid_stretch.index(c) < remainder else 0)
                        self.table.setColumnWidth(c, w + bonus)
                    else:
                        self.table.setColumnWidth(c, w)
                return

        # Fallback to pure min widths when space is tight
        for c in range(col_count):
            w = self._min_widths[c] if c < len(self._min_widths) else 100
            self.table.setColumnWidth(c, w)

    def set_search_placeholder(self, placeholder: str):
        """Change the search input placeholder text."""
        self.search_input.setPlaceholderText(placeholder)

    def set_add_button_text(self, text: str):
        """Sets the label for the add button."""
        self.add_btn.setText(text)

    def set_add_button_visible(self, visible: bool):
        """Sets whether the add button is visible."""
        self.add_btn.setVisible(visible)

    def set_record_count(self, current_count: int, total_count: int):
        """Update footer label and switch table/empty-state widget."""
        self.update_info(current_count, total_count)

    def update_info(self, current_count: int, total_count: int):
        """Show table if records exist, otherwise show empty state."""
        if current_count == 0:
            self.content_stack.setCurrentWidget(self.empty_state)
        else:
            self.content_stack.setCurrentWidget(self.table)
        self.info_label.setText(
            tr("common.showing_records", count=current_count, total=total_count)
        )
        self.adjust_column_widths()

    def retranslate_ui(self):
        self.search_input.setPlaceholderText(tr("common.search_placeholder"))
        self.refresh_btn.setText(tr("common.refresh"))
        self.add_btn.setText(tr("common.add"))
        if self.header_keys:
            translated_headers = [tr(k) for k in self.header_keys]
            self.set_headers(translated_headers, self.header_keys)
        self.adjust_column_widths()
