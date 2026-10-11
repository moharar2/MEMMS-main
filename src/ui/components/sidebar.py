"""
Enterprise Sidebar Navigation component.
Pure Arabic RTL, collapsible folder sections (Accordion), high-contrast vector icons, zero emojis.
Ensures strict Right-to-Left alignment where icon is on the right, text is beside it, and folder chevrons toggle smoothly on the left.
"""
from typing import Dict, List, Tuple
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QFrame,
    QScrollArea, QHBoxLayout
)
from PySide6.QtCore import Qt, Signal
from src.ui.theme.icons import icon


class NavButton(QPushButton):
    """
    Sub-item navigation button within a category folder.
    """
    def __init__(self, key: str, icon_name: str, label_text: str, parent=None):
        super().__init__("", parent)
        self.key = key
        self.icon_name = icon_name
        self.label_text = label_text
        self.setCheckable(True)
        self.setFixedHeight(38)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        # Internal Layout: [Right Gap/Indentation] [Icon on the right] [Gap 10px] [Text] [Stretch on left]
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 10, 0)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.icon_label = QLabel()
        self.icon_label.setFixedSize(16, 16)
        self.icon_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.icon_label.setStyleSheet("background: transparent;")
        self.icon_label.setPixmap(icon(icon_name, color="#94A3B8", size=15).pixmap(15, 15))

        self.text_label = QLabel(label_text)
        self.text_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.text_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #E2E8F0; background: transparent;")

        layout.addWidget(self.icon_label)
        layout.addWidget(self.text_label)
        layout.addStretch()

        self._update_appearance(False)

    def _update_appearance(self, is_active: bool):
        if is_active:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #0F766E;
                    border: none;
                    border-radius: 6px;
                }
                QPushButton:hover {
                    background-color: #0D9488;
                }
            """)
            self.icon_label.setPixmap(icon(self.icon_name, color="#FFFFFF", size=15).pixmap(15, 15))
            self.text_label.setStyleSheet("font-size: 13px; font-weight: 700; color: #FFFFFF; background: transparent;")
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: none;
                    border-radius: 6px;
                }
                QPushButton:hover {
                    background-color: #1E293B;
                }
            """)
            self.icon_label.setPixmap(icon(self.icon_name, color="#94A3B8", size=15).pixmap(15, 15))
            self.text_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #CBD5E1; background: transparent;")

    def set_active_state(self, active: bool):
        self.setChecked(active)
        self._update_appearance(active)

    def update_text(self, text: str):
        self.label_text = text
        self.text_label.setText(text)
        self._update_appearance(self.isChecked())


class NavSectionHeader(QPushButton):
    """
    Collapsible Folder / Category Header.
    Displays folder icon and title on the right, chevron toggle on the left.
    """
    toggled_expansion = Signal(bool)

    def __init__(self, title: str, is_expanded: bool = True, parent=None):
        super().__init__("", parent)
        self.title = title
        self.is_expanded = is_expanded
        self.setFixedHeight(34)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        # Folder Icon (Right)
        self.folder_icon = QLabel()
        self.folder_icon.setFixedSize(16, 16)
        self.folder_icon.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.folder_icon.setStyleSheet("background: transparent;")

        # Section Title (Right beside folder)
        self.title_label = QLabel(title)
        self.title_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.title_label.setStyleSheet("font-size: 11.5px; font-weight: 800; color: #94A3B8; background: transparent;")

        # Chevron Indicator (Left)
        self.chevron_icon = QLabel()
        self.chevron_icon.setFixedSize(14, 14)
        self.chevron_icon.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.chevron_icon.setStyleSheet("background: transparent;")

        layout.addWidget(self.folder_icon)
        layout.addWidget(self.title_label)
        layout.addStretch()
        layout.addWidget(self.chevron_icon)

        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #1E293B;
            }
        """)

        self.clicked.connect(self._toggle)
        self._update_icons()

    def _toggle(self):
        self.set_expanded(not self.is_expanded)
        self.toggled_expansion.emit(self.is_expanded)

    def set_expanded(self, expanded: bool):
        self.is_expanded = expanded
        self._update_icons()

    def _update_icons(self):
        if self.is_expanded:
            self.folder_icon.setPixmap(icon("folder_open", color="#14B8A6", size=14).pixmap(14, 14))
            # In RTL layout, chevron pointing down means open
            self.chevron_icon.setPixmap(icon("chevron_down", color="#94A3B8", size=11).pixmap(11, 11))
            self.title_label.setStyleSheet("font-size: 11.5px; font-weight: 800; color: #E2E8F0; background: transparent;")
        else:
            self.folder_icon.setPixmap(icon("folder", color="#64748B", size=14).pixmap(14, 14))
            # In RTL layout, chevron pointing left means collapsed/expandable
            self.chevron_icon.setPixmap(icon("chevron_left", color="#64748B", size=11).pixmap(11, 11))
            self.title_label.setStyleSheet("font-size: 11.5px; font-weight: 700; color: #64748B; background: transparent;")


class CollapsibleNavSection(QWidget):
    """
    Folder section containing a clickable header and expandable item container.
    """
    def __init__(self, title: str, items: List[Tuple[str, str, str]], on_item_clicked, parent=None):
        super().__init__(parent)
        self.title = title
        self.keys: List[str] = [k for k, _, _ in items]
        self.buttons: Dict[str, NavButton] = {}
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(2)

        # 1. Header
        self.header = NavSectionHeader(title, is_expanded=True)
        self.header.toggled_expansion.connect(self._on_header_toggled)
        layout.addWidget(self.header)

        # 2. Items Container (Sub-items)
        self.items_container = QWidget()
        self.items_container.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.items_container.setStyleSheet("background: transparent;")
        items_layout = QVBoxLayout(self.items_container)
        items_layout.setContentsMargins(6, 2, 6, 2)
        items_layout.setSpacing(2)

        for key, icon_name, label_text in items:
            btn = NavButton(key, icon_name, label_text)
            btn.clicked.connect(lambda _, k=key: on_item_clicked(k))
            self.buttons[key] = btn
            items_layout.addWidget(btn)

        layout.addWidget(self.items_container)

    def _on_header_toggled(self, is_expanded: bool):
        self.items_container.setVisible(is_expanded)

    def expand(self):
        self.header.set_expanded(True)
        self.items_container.setVisible(True)

    def collapse(self):
        self.header.set_expanded(False)
        self.items_container.setVisible(False)

    def is_expanded(self) -> bool:
        return self.header.is_expanded


class Sidebar(QWidget):
    navigation_changed = Signal(str)

    # Clean, logical category structure
    SECTIONS = [
        ("الرئيسية", [
            ("dashboard", "dashboard", "لوحة المؤشرات"),
        ]),
        ("إدارة الأجهزة والمواقع", [
            ("equipment", "equipment", "الأجهزة الطبية"),
            ("departments", "departments", "الأقسام والمواقع"),
        ]),
        ("عمليات الصيانة", [
            ("work_orders", "work_orders", "أوامر الصيانة والبلاغات"),
            ("preventive", "preventive", "الصيانة الوقائية والمعايرة"),
        ]),
        ("المستودع والكوادر", [
            ("inventory", "inventory", "المستودع وقطع الغيار"),
            ("technicians", "technicians", "الكادر الفني والمهندسون"),
            ("vendors", "vendors", "الشركات والموردون"),
            ("contracts", "contracts", "عقود الصيانة والضمان"),
        ]),
        ("التقارير والنظام", [
            ("reports", "reports", "التقارير والتحليلات"),
            ("audit_logs", "audit_logs", "سجل العمليات"),
            ("users", "users", "المستخدمون والأدوار"),
            ("settings", "settings", "إعدادات النظام"),
        ])
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SidebarRoot")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setFixedWidth(260)
        self.buttons: Dict[str, NavButton] = {}
        self.sections: List[CollapsibleNavSection] = []

        # Solid Dark navy background throughout the entire widget tree
        self.setStyleSheet("""
            QWidget#SidebarRoot {
                background-color: #0F172A;
                border-left: 1px solid #1E293B;
            }
            QScrollArea, QScrollArea > QWidget, QScrollArea > QWidget > QWidget {
                background-color: #0F172A;
                border: none;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 14, 10, 14)
        main_layout.setSpacing(6)

        # 1. Brand Header (Right-to-Left)
        brand_frame = QFrame()
        brand_frame.setObjectName("BrandFrame")
        brand_frame.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        brand_frame.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        brand_frame.setStyleSheet("""
            QFrame#BrandFrame {
                background-color: #0F172A;
                border-bottom: 1px solid #1E293B;
                padding-bottom: 12px;
                margin-bottom: 6px;
            }
        """)
        brand_layout = QHBoxLayout(brand_frame)
        brand_layout.setContentsMargins(8, 4, 8, 8)
        brand_layout.setSpacing(12)
        brand_layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        brand_icon = QLabel()
        brand_icon.setPixmap(icon("hospital_brand", color="#14B8A6", size=26).pixmap(26, 26))

        titles_layout = QVBoxLayout()
        titles_layout.setSpacing(1)

        self.title_lbl = QLabel("MEMMS")
        self.title_lbl.setStyleSheet("font-size: 20px; font-weight: 800; color: #14B8A6; letter-spacing: 1px;")
        self.title_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.sub_lbl = QLabel("إدارة الصيانة الطبية")
        self.sub_lbl.setStyleSheet("font-size: 11px; color: #94A3B8; font-weight: 600;")
        self.sub_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)

        titles_layout.addWidget(self.title_lbl)
        titles_layout.addWidget(self.sub_lbl)

        brand_layout.addWidget(brand_icon)
        brand_layout.addLayout(titles_layout)
        brand_layout.addStretch()
        main_layout.addWidget(brand_frame)

        # 2. Navigation Scroll Area
        scroll = QScrollArea()
        scroll.setObjectName("SidebarScroll")
        scroll.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        if scroll.viewport():
            scroll.viewport().setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background-color: #0F172A; border: none;")

        scroll_content = QWidget()
        scroll_content.setObjectName("SidebarScrollContent")
        scroll_content.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        scroll_content.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        scroll_content.setStyleSheet("background-color: #0F172A;")
        self.scroll_layout = QVBoxLayout(scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(4)

        # Build collapsible folder sections
        for sec_title, items in self.SECTIONS:
            sec = CollapsibleNavSection(sec_title, items, self._on_btn_clicked)
            self.sections.append(sec)
            for k, btn in sec.buttons.items():
                self.buttons[k] = btn
            self.scroll_layout.addWidget(sec)

        self.scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll, stretch=1)

    def _on_btn_clicked(self, active_key: str):
        self.set_active_key(active_key)
        self.navigation_changed.emit(active_key)

    def set_active_key(self, key: str):
        for k, btn in self.buttons.items():
            is_active = (k == key)
            btn.set_active_state(is_active)
            if is_active:
                # Ensure the containing section is expanded
                for sec in self.sections:
                    if key in sec.keys and not sec.is_expanded():
                        sec.expand()

    def set_active(self, key: str):
        self.set_active_key(key)

    def retranslate_ui(self):
        pass
