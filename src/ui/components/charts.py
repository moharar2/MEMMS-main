"""
Lightweight, crisp vector charts for the MEMMS Dashboard using QPainter.
Zero external dependencies, high-performance, and theme-adaptive.
"""
from typing import Dict, List, Tuple
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont
from PySide6.QtCore import Qt, QRectF
from src.core.i18n import tr


class DonutStatusChart(QWidget):
    """
    Renders an elegant donut chart for equipment operational statuses.
    """
    def __init__(self, data: Dict[str, Tuple[int, str]], parent=None):
        super().__init__(parent)
        self.data = data  # key -> (count, color_hex)
        self.setMinimumHeight(180)

    def set_data(self, data: Dict[str, Tuple[int, str]]):
        self.data = data
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        total = sum(item[0] for item in self.data.values())
        rect = self.rect()
        size = min(rect.width(), rect.height()) - 20
        chart_rect = QRectF((rect.width() - size) / 2, (rect.height() - size) / 2, size, size)

        if total == 0:
            # Draw placeholder ring
            painter.setPen(QPen(QColor("#E2E8F0"), 16))
            painter.drawEllipse(chart_rect)
            painter.setPen(QColor("#94A3B8"))
            painter.setFont(QFont("Segoe UI", 11))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, tr("common.no_data"))
            painter.end()
            return

        start_angle = 90 * 16
        pen_width = 22

        for key, (count, color_hex) in self.data.items():
            if count <= 0:
                continue
            span_angle = int(-(count / total) * 360 * 16)
            pen = QPen(QColor(color_hex), pen_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.FlatCap)
            painter.setPen(pen)
            inner_rect = chart_rect.adjusted(pen_width/2, pen_width/2, -pen_width/2, -pen_width/2)
            painter.drawArc(inner_rect, start_angle, span_angle)
            start_angle += span_angle

        # Draw central total text
        painter.setPen(QColor("#0F172A"))
        font_num = QFont("Segoe UI", 16, QFont.Weight.Bold)
        painter.setFont(font_num)
        painter.drawText(rect.adjusted(0, -10, 0, 0), Qt.AlignmentFlag.AlignCenter, str(total))

        painter.setPen(QColor("#64748B"))
        font_lbl = QFont("Segoe UI", 10)
        painter.setFont(font_lbl)
        painter.drawText(rect.adjusted(0, 30, 0, 0), Qt.AlignmentFlag.AlignCenter, tr("dashboard.total_equipment"))

        painter.end()


class BarPriorityChart(QWidget):
    """
    Renders a clean horizontal bar comparison chart for priorities or categories.
    """
    def __init__(self, data: List[Tuple[str, int, str]], parent=None):
        super().__init__(parent)
        self.data = data  # list of (label_text, count, color_hex)
        self.setMinimumHeight(180)

    def set_data(self, data: List[Tuple[str, int, str]]):
        self.data = data
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if not self.data:
            painter.end()
            return

        max_val = max([item[1] for item in self.data] or [1])
        if max_val == 0:
            max_val = 1

        rect = self.rect()
        row_height = rect.height() / max(len(self.data), 1)
        bar_height = 14
        label_width = 110

        font_label = QFont("Segoe UI", 11, QFont.Weight.Medium)
        font_val = QFont("Segoe UI", 11, QFont.Weight.Bold)

        for i, (label, count, color_hex) in enumerate(self.data):
            y = int(i * row_height + (row_height - bar_height) / 2)

            # Draw Label
            painter.setPen(QColor("#334155"))
            painter.setFont(font_label)
            painter.drawText(10, y + 12, label_width, bar_height + 4, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, label)

            # Draw Bar Background Track
            track_x = label_width + 20
            track_w = rect.width() - track_x - 50
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#F1F5F9"))
            painter.drawRoundedRect(track_x, y, track_w, bar_height, 4, 4)

            # Draw Progress Fill
            fill_w = int((count / max_val) * track_w)
            if fill_w > 0:
                painter.setBrush(QColor(color_hex))
                painter.drawRoundedRect(track_x, y, fill_w, bar_height, 4, 4)

            # Draw Value Number
            painter.setPen(QColor("#0F172A"))
            painter.setFont(font_val)
            val_x = track_x + track_w + 10
            painter.drawText(val_x, y + 12, 35, bar_height + 4, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, str(count))

        painter.end()
