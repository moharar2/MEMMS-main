"""
Test UI flow for LoginWindow and MainWindow to prevent regression of recursion or crash.
"""
import pytest
from PySide6.QtWidgets import QApplication
from src.ui.main_window import MainWindow
from src.services.auth_service import auth_service
from src.models.user import User


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_main_window_creation_and_navigation(qapp, test_db):
    admin = test_db.query(User).filter_by(username="admin").first()
    auth_service.set_current_user(admin)

    # Creating MainWindow must not raise RecursionError
    window = MainWindow()
    assert window is not None

    # Test navigation to different tabs
    window.navigate_to("equipment")
    assert window.stack.currentWidget() == window.equipment_view

    window.navigate_to("departments")
    assert window.stack.currentWidget() == window.departments_view

    window.navigate_to("vendors")
    assert window.stack.currentWidget() == window.vendors_view

    window.navigate_to("dashboard")
    assert window.stack.currentWidget() == window.dashboard_view

    window.close()
