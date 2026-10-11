"""
Tests for UI/UX Redesign, Zero Emojis, and Pure Arabic RTL Localization.
"""
import re
from pathlib import Path
import pytest
from PySide6.QtWidgets import QApplication
from src.core.i18n import i18n, tr
from src.ui.theme.icons import IconHelper, icon
from src.ui.main_window import MainWindow
from src.services.auth_service import auth_service
from src.models import User
from src.ui.views.equipment_details_dialog import EquipmentDetailsDialog
from src.ui.views.work_order_dialog import WorkOrderDialog


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_zero_emojis_in_source_code():
    """Verifies that no emoji unicode characters exist anywhere in src/ui or locales."""
    emoji_pattern = re.compile(r"[\U0001F300-\U0001F9FF\U00002600-\U000026FF\U00002700-\U000027BF]")
    project_root = Path(__file__).resolve().parent.parent

    scanned_files = []
    for ext in ("*.py",):
        scanned_files.extend(list((project_root / "src").rglob(ext)))

    assert len(scanned_files) > 0

    found_emojis = []
    for f in scanned_files:
        content = f.read_text(encoding="utf-8")
        matches = emoji_pattern.findall(content)
        if matches:
            found_emojis.append((str(f.name), matches))

    assert len(found_emojis) == 0, f"Found emojis in files: {found_emojis}"


def test_icon_helper_returns_valid_icons(qapp):
    """Verifies that IconHelper returns non-null QIcon instances for standard semantic keys."""
    for key in IconHelper.ICONS.keys():
        ic = icon(key)
        assert ic is not None
        assert not ic.isNull()


def test_arabic_rtl_ui_state(qapp, test_db):
    """Tests Arabic RTL state and elements on MainWindow."""
    admin = test_db.query(User).filter_by(username="admin").first()
    auth_service.set_current_user(admin)

    window = MainWindow()
    assert i18n.current_locale == "ar"
    assert i18n.is_rtl() is True
    assert tr("app.logout") == "تسجيل الخروج"
    assert window.navbar.logout_btn.text() == "تسجيل الخروج"

    window.close()


def test_equipment_details_and_work_order_dialogs(qapp, test_db):
    """Tests opening EquipmentDetailsDialog and WorkOrderDialog without errors."""
    admin = test_db.query(User).filter_by(username="admin").first()
    auth_service.set_current_user(admin)

    from src.services.hospital_service import hospital_service
    from src.services.equipment_service import equipment_service

    dept = hospital_service.create_department(test_db, admin, {"name_ar": "قسم الاختبار", "code": "TST-01"})
    eq = equipment_service.create_equipment(test_db, admin, {
        "asset_number": "EQ-DET-01",
        "serial_number": "SN-DET-01",
        "name_ar": "جهاز تخطيط قلب",
        "name_en": "ECG Machine",
        "department_id": dept.id,
        "category": "ECG"
    })

    # Details dialog
    details_dlg = EquipmentDetailsDialog(equipment=eq)
    assert details_dlg is not None
    details_dlg.close()

    # Work order dialog
    wo_dlg = WorkOrderDialog()
    assert wo_dlg is not None
    wo_dlg.close()
