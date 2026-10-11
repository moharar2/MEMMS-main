"""
staff_phase3_test.py
--------------------
Comprehensive automated test suite for Phase 3 (Staff Management & Modern UI).
"""

import os
import sys
from datetime import date
from pathlib import Path

os.environ["QT_QPA_PLATFORM"] = "offscreen"
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtWidgets import QApplication
app = QApplication.instance() or QApplication(sys.argv)

from database import get_session, init_db
from models import Department, Equipment, Staff, WorkOrder
from app.translations import Translator, LANG_AR, LANG_EN
from app.main_window import MainWindow
from app.staff_page import StaffPage
from app.staff_dialog import StaffDialog


def run_tests():
    print("=== Step 1: Database Initialization & Integrity ===")
    init_db()

    with get_session() as s:
        eq_count = s.query(Equipment).count()
        dept_count = s.query(Department).count()
        print(f"Equipment count preserved: {eq_count}")
        print(f"Department count initialized: {dept_count}")
        assert dept_count >= 6, "Expected default departments to be seeded"

    print("\n=== Step 2: Main Window & Navigation Integration ===")
    translator = Translator(initial_lang=LANG_AR)
    window = MainWindow(translator)
    window.show()
    app.processEvents()

    # Verify staff page is in the stack
    assert isinstance(window._staff_page, StaffPage), "StaffPage should be instantiated"
    
    # Navigate to Staff page
    window._show_page("staff")
    app.processEvents()
    assert window._stack.currentIndex() == 5, f"Expected page index 5, got {window._stack.currentIndex()}"
    print("Navigation to Staff page verified successfully.")

    print("\n=== Step 3: Staff CRUD & Validation ===")
    # 1. Create Staff
    with get_session() as s:
        # Clear existing test staff
        s.query(Staff).filter(Staff.staff_code.like("TEST-%")).delete()
        s.commit()

        d = s.query(Department).first()
        dept_id = d.id if d else None

        new_staff = Staff(
            staff_code="TEST-001",
            full_name="م. سارة أحمد",
            position="مهندس أجهزة طبية",
            specialization="أشعة ورنين مغناطيسي",
            department_id=dept_id,
            phone="0501234567",
            email="sara@hospital.med",
            hire_date=date(2024, 1, 15),
            is_active=True,
            notes="مسؤولة أجهزة الأشعة",
        )
        s.add(new_staff)
        s.commit()

    # Verify insertion
    with get_session() as s:
        staff_db = s.query(Staff).filter_by(staff_code="TEST-001").first()
        assert staff_db is not None, "Staff should exist in DB"
        assert staff_db.full_name == "م. سارة أحمد"
        assert staff_db.staff_id == "TEST-001"  # property alias
        assert staff_db.status == "active"       # property alias
        print("Staff member created and verified successfully.")

    # 2. Staff Page UI Refresh & Mini Stats
    window._staff_page.refresh()
    app.processEvents()
    assert int(window._staff_page.stat_total.lbl_val.text()) >= 1, "Total stats should reflect staff count"
    assert int(window._staff_page.stat_active.lbl_val.text()) >= 1, "Active stats should reflect staff count"
    print("Staff UI table and stat badges updated.")

    # 3. Test Search and Filtering
    window._staff_page.search_input.setText("سارة")
    app.processEvents()
    assert window._staff_page.table.rowCount() == 1, "Search should filter table to 1 row"

    window._staff_page.search_input.setText("NON_EXISTENT_QUERY_999")
    app.processEvents()
    assert window._staff_page.table.rowCount() == 0, "Non-existent search should result in 0 rows"

    window._staff_page._reset_filters()
    app.processEvents()
    assert window._staff_page.table.rowCount() >= 1, "Reset filters should restore rows"
    print("Search and filtering verified.")

    # 4. Bilingual RTL / LTR Switching
    print("\n=== Step 4: Bilingual Switching ===")
    window._on_language_button_clicked()  # Switch to English
    app.processEvents()
    assert translator.lang == LANG_EN
    assert window._top_title.text() == "Staff"
    assert window._staff_page.heading.text() == "Staff & Technicians Management"
    print("English LTR translation verified.")

    window._on_language_button_clicked()  # Switch back to Arabic
    app.processEvents()
    assert translator.lang == LANG_AR
    assert window._top_title.text() == "العاملون"
    assert window._staff_page.heading.text() == "إدارة الكادر الفني والموظفين"
    print("Arabic RTL translation verified.")

    # Clean up test staff
    with get_session() as s:
        s.query(Staff).filter(Staff.staff_code.like("TEST-%")).delete()
        s.commit()

    print("\n=============================================")
    print(" ALL PHASE 3 TESTS PASSED SUCCESSFULLY! ")
    print("=============================================")


if __name__ == "__main__":
    run_tests()
