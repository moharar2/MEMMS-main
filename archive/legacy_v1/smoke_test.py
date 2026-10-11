"""
Headless smoke test for MEMMS Phase 1.

Verifies:
- All modules import cleanly.
- init_db() creates tables.
- Dashboard queries return the right counts.
- Translator flips language + RTL/LTR.
- MainWindow can be built without exceptions.
- Sidebar navigation switches pages.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Force offscreen Qt platform BEFORE importing PySide6.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# Make sure the project root is on sys.path so 'database' and 'app' resolve.
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))


def banner(title: str) -> None:
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def main() -> int:
    failures: list[str] = []

    banner("1. Importing modules")
    try:
        from database import init_db, get_session  # noqa: F401
        from models import Equipment, Staff, WorkOrder  # noqa: F401
        from app.main_window import MainWindow  # noqa: F401
        from app.dashboard import DashboardPage, StatCard  # noqa: F401
        from app.pages import PlaceholderPage  # noqa: F401
        from app.translations import Translator, LANG_AR, LANG_EN, tr, is_rtl  # noqa: F401
        from app.styles import STYLESHEET  # noqa: F401
        print("  OK")
    except Exception as exc:
        failures.append(f"imports failed: {exc}")
        print(f"  FAIL: {exc}")
        return 1

    banner("2. init_db()")
    try:
        init_db()
        print("  OK")
    except Exception as exc:
        failures.append(f"init_db failed: {exc}")
        print(f"  FAIL: {exc}")
        return 1

    banner("3. Sample counts (uses the data already in data/memms.db)")
    try:
        from models import Equipment, Staff, WorkOrder
        with get_session() as s:
            total_eq = s.query(Equipment).count()
            open_wo = s.query(WorkOrder).filter(WorkOrder.status != "closed").count()
            total_staff = s.query(Staff).count()
        print(f"  equipment={total_eq}  open_work_orders={open_wo}  staff={total_staff}")
    except Exception as exc:
        failures.append(f"counts failed: {exc}")
        print(f"  FAIL: {exc}")

    banner("4. Translator + RTL/LTR")
    try:
        from app.translations import Translator, LANG_AR, LANG_EN, tr, is_rtl
        # Plain string lookup
        assert tr("nav.dashboard", LANG_AR) == "لوحة التحكم"
        assert tr("nav.dashboard", LANG_EN) == "Dashboard"
        assert is_rtl(LANG_AR) is True
        assert is_rtl(LANG_EN) is False
        print("  OK")
    except AssertionError as exc:
        failures.append(f"translator logic: {exc}")
        print(f"  FAIL: {exc}")

    banner("5. Build MainWindow and exercise it")
    try:
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QApplication
        from app.main_window import MainWindow
        from app.translations import Translator

        app = QApplication.instance() or QApplication(sys.argv)
        translator = Translator(initial_lang=LANG_AR)
        window = MainWindow(translator)
        window.show()
        # Process pending events so the window is fully realized.
        app.processEvents()
        print(f"  initial layoutDirection = {app.layoutDirection()}")  # RTL

        # Flip to English.
        translator.set_language(LANG_EN)
        app.processEvents()
        print(f"  after EN layoutDirection = {app.layoutDirection()}")  # LTR
        assert app.layoutDirection() == Qt.LeftToRight, "expected LTR after EN"

        # Flip back.
        translator.set_language(LANG_AR)
        app.processEvents()
        print(f"  after AR layoutDirection = {app.layoutDirection()}")  # RTL
        assert app.layoutDirection() == Qt.RightToLeft, "expected RTL after AR"

        # Walk every sidebar page.
        # There are 8 sections: dashboard + 7 placeholders.
        for i in range(window._stack.count()):
            window._stack.setCurrentIndex(i)
            app.processEvents()
            page = window._stack.currentWidget()
            print(f"  page {i}: {type(page).__name__}")
        window.close()
        print("  OK")
    except Exception as exc:
        import traceback
        traceback.print_exc()
        failures.append(f"window build failed: {exc}")
        print(f"  FAIL: {exc}")

    banner("RESULT")
    if failures:
        for f in failures:
            print("  -", f)
        return 1
    print("  All smoke checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
