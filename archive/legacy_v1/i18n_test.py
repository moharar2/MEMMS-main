"""Verify that every sidebar entry retranslates its page title on switch."""
import os
import sys
from pathlib import Path

os.environ["QT_QPA_PLATFORM"] = "offscreen"
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtWidgets import QApplication
app = QApplication.instance() or QApplication(sys.argv)

from database import init_db
from app.main_window import MainWindow
from app.translations import Translator, LANG_AR, LANG_EN

init_db()

translator = Translator(initial_lang=LANG_AR)
window = MainWindow(translator)
window.show()
app.processEvents()

# Expected page titles in each language.
EXPECT_AR = {
    "dashboard":   "لوحة التحكم",
    "equipment":   "الأجهزة الطبية",
    "work_orders": "أوامر الصيانة",
    "preventive":  "الصيانة الوقائية",
    "spare_parts": "قطع الغيار",
    "staff":       "العاملون",
    "reports":     "التقارير والإحصائيات",
    "settings":    "الإعدادات",
}
EXPECT_EN = {
    "dashboard":   "Dashboard",
    "equipment":   "Medical Equipment",
    "work_orders": "Work Orders",
    "preventive":  "Preventive Maintenance",
    "spare_parts": "Spare Parts",
    "staff":       "Staff",
    "reports":     "Reports & Statistics",
    "settings":    "Settings",
}

# Click each nav button in Arabic, capture the top title + page title.
page_ids = ["dashboard", "equipment", "work_orders", "preventive",
            "spare_parts", "staff", "reports", "settings"]

def click_button_for(btn_page_id):
    for btn, pid in zip(window._nav_buttons, window._nav_page_ids):
        if pid == btn_page_id:
            btn.click()
            return

for pid in page_ids:
    click_button_for(pid)
    app.processEvents()
    top = window._top_title.text()
    expected = EXPECT_AR[pid]
    assert top == expected, f"AR {pid}: top title {top!r} != {expected!r}"

# Switch language.
translator.set_language(LANG_EN)
app.processEvents()

for pid in page_ids:
    click_button_for(pid)
    app.processEvents()
    top = window._top_title.text()
    expected = EXPECT_EN[pid]
    assert top == expected, f"EN {pid}: top title {top!r} != {expected!r}"

print("OK: all 8 pages retranslate correctly on AR/EN switch.")
