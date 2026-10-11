"""Verify that the dashboard refresh button updates the cards in real time."""
import os
import sys
from pathlib import Path

os.environ["QT_QPA_PLATFORM"] = "offscreen"
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from datetime import date
from decimal import Decimal

from PySide6.QtWidgets import QApplication
app = QApplication.instance() or QApplication(sys.argv)

from database import get_session, init_db
from models import Department, Equipment, MaintenancePlan, SparePart, Staff, WorkOrder
from app.translations import Translator, LANG_AR
from app.dashboard import DashboardPage
from app.main_window import MainWindow

init_db()

translator = Translator(initial_lang=LANG_AR)
window = MainWindow(translator)
window.show()
app.processEvents()

# Wipe and reseed so we start from a known count.
with get_session() as s:
    s.query(WorkOrder).delete()
    s.query(MaintenancePlan).delete()
    s.query(Equipment).delete()
    s.query(Staff).delete()
    s.query(Department).delete()
    s.query(SparePart).delete()
    s.commit()

# Insert 3 equipment, 1 staff, 2 open work orders.
with get_session() as s:
    d = Department(name_ar='قسم', name_en='ICU', location='B1')
    s.add(d); s.flush()
    s.add(Staff(full_name='Test User', position='Tech', department_id=d.id, is_active=True))
    s.flush()
    for code in ('EQ-A', 'EQ-B', 'EQ-C'):
        s.add(Equipment(hospital_code=code, name_ar='جهاز', name_en=f'Device {code}',
                        department_id=d.id, status='operational'))
    s.flush()
    eqs = s.query(Equipment).all()
    for eq in eqs[:2]:
        s.add(WorkOrder(order_number=f'WO-{eq.hospital_code}', equipment_id=eq.id,
                        maintenance_type='corrective', status='open'))
    s.commit()

# Trigger refresh.
window._dashboard.refresh_stats()
app.processEvents()

eq_val = window._dashboard.card_equipment.value_label.text()
wo_val = window._dashboard.card_work_orders.value_label.text()
st_val = window._dashboard.card_staff.value_label.text()

print(f"After refresh: equipment={eq_val} work_orders={wo_val} staff={st_val}")

assert eq_val == '3', f"expected 3 equipment, got {eq_val}"
assert wo_val == '2', f"expected 2 open work orders, got {wo_val}"
assert st_val == '1', f"expected 1 staff, got {st_val}"

# Now switch to English and confirm the card title text changes.
translator.set_language("en")
app.processEvents()
en_title = window._dashboard.card_equipment.title_label.text()
ar_title_before = "إجمالي الأجهزة"  # what we expect in AR
print(f"Card title after EN switch: {en_title!r}")
assert en_title == "Total Equipment", f"expected 'Total Equipment', got {en_title!r}"

print("OK: dashboard refresh + language switch work end-to-end.")
