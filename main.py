"""
MEMMS — Medical Equipment Maintenance Management System
Main entry point for the desktop application.
"""
import sys
from datetime import date
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

from config import APP_NAME, DEFAULT_LOCALE
from src.core.database import init_db, get_db
from src.core.i18n import i18n
from src.models import Hospital, Department, Location, Vendor, Equipment, User


def ensure_initial_master_data():
    """
    Ensures baseline hospital record exists if database is newly initialized.
    Does not insert mock equipment so that real user workflows operate on clean data.
    """
    with get_db() as db:
        if db.query(Hospital).count() == 0:
            hosp = Hospital(
                name_ar="مستشفى الملك فهد التخصصي",
                name_en="King Fahd Specialist Hospital",
                code="KFSH-01",
                address="الرياض، المملكة العربية السعودية",
                phone="0114005000",
                is_active=True
            )
            db.add(hosp)
            db.flush()

            # Baseline primary departments
            dept_icu = Department(hospital_id=hosp.id, name_ar="العناية المركزة (ICU)", name_en="Intensive Care Unit", code="ICU", floor="الطابق 3")
            dept_rad = Department(hospital_id=hosp.id, name_ar="قسم الأشعة والتصوير الطبي", name_en="Radiology Department", code="RAD", floor="الطابق الأرضي")
            dept_surg = Department(hospital_id=hosp.id, name_ar="غرف العمليات الجراحية", name_en="Operating Rooms (OR)", code="OR", floor="الطابق 2")
            dept_dial = Department(hospital_id=hosp.id, name_ar="مركز الغسيل الكلوي", name_en="Dialysis Center", code="DIA", floor="الطابق 1")
            db.add_all([dept_icu, dept_rad, dept_surg, dept_dial])
            db.flush()

            # Baseline room locations
            loc_icu_1 = Location(department_id=dept_icu.id, room_number="ICU-101", room_name="غرفة العناية الفائقة 1")
            loc_icu_2 = Location(department_id=dept_icu.id, room_number="ICU-102", room_name="غرفة العناية الفائقة 2")
            loc_rad_1 = Location(department_id=dept_rad.id, room_number="RAD-01", room_name="غرفة الأشعة CT")
            db.add_all([loc_icu_1, loc_icu_2, loc_rad_1])
            db.flush()

            # Baseline vendors
            v_ge = Vendor(name="GE Healthcare", vendor_type="manufacturer", contact_person="م. طارق", phone="0550001111", email="support@ge-health.sa")
            v_siemens = Vendor(name="Siemens Healthineers", vendor_type="manufacturer", contact_person="م. سارة", phone="0550002222", email="service@siemens.sa")
            v_supplier = Vendor(name="الشركة الخليجية للمعدات الطبية", vendor_type="supplier", contact_person="محمد العتيبي", phone="0550004444", email="sales@gulfmed.sa")
            db.add_all([v_ge, v_siemens, v_supplier])
            db.commit()


class AppController:
    def __init__(self):
        self.main_window = None
        self.login_window = None

    def start(self):
        self.show_login()

    def show_login(self):
        from src.ui.login_window import LoginWindow
        if self.main_window:
            self.main_window.close()
            self.main_window = None

        self.login_window = LoginWindow()
        self.login_window.login_successful.connect(self.on_login_success)
        self.login_window.show()

    def on_login_success(self, user):
        from src.ui.main_window import MainWindow
        self.login_window = None
        self.main_window = MainWindow()
        self.main_window.logout_requested.connect(self.show_login)
        self.main_window.show()


def install_crash_handler():
    """
    Installs a global exception hook to catch and log any startup/runtime crashes
    when running as a frozen executable (.exe).
    """
    import traceback
    from config import LOGS_DIR
    from PySide6.QtWidgets import QMessageBox

    def excepthook(exc_type, exc_value, exc_tb):
        err_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        log_file = LOGS_DIR / "crash.log"
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"\n--- CRASH REPORT ---\n{err_msg}\n")
        except Exception:
            pass

        app = QApplication.instance()
        if app:
            try:
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Icon.Critical)
                msg_box.setWindowTitle("خطأ في تشغيل النظام — MEMMS")
                msg_box.setText("حدث خطأ أثناء تشغيل النظام. تم تسجيل التفاصيل في ملف crash.log.")
                msg_box.setDetailedText(err_msg)
                msg_box.exec()
            except Exception:
                pass
        sys.__excepthook__(exc_type, exc_value, exc_tb)

    sys.excepthook = excepthook


def main():
    # 0. Setup crash reporting
    install_crash_handler()

    # 1. Setup Qt Application with RTL Layout
    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    app.setApplicationName(APP_NAME)

    # 2. Configure Arabic Typography & Light Theme
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    i18n.set_locale("ar")
    from src.ui.theme.theme_manager import theme_manager
    theme_manager.apply_theme()

    # 3. Initialize Database Schema & Admin
    init_db()
    ensure_initial_master_data()

    # 4. Trigger Automated Monthly Reports Catch-up (Startup)
    try:
        from src.services.monthly_report_service import monthly_report_service
        with get_db() as db:
            monthly_report_service.check_and_run_startup_catchup(db)
    except Exception as e:
        print(f"[MEMMS] Warning: Monthly reports startup catch-up failed: {e}")

    # 5. Launch Application Controller
    controller = AppController()
    controller.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

