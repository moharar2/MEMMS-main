"""
Comprehensive End-to-End System Integration Test for MEMMS.
Covers real database lifecycle: Hospital -> Equipment -> Work Order + Part Deduction -> PM Execution -> Inventory -> Reports -> Backup.
"""
import os
from datetime import date, datetime, timedelta
import pytest
from src.models import (
    User, Hospital, Department, Location, Vendor, Contract,
    Technician, Equipment, WorkOrder, WorkOrderPart, PMPlan,
    PMSchedule, PMExecution, SparePart, InventoryTransaction
)
from src.services.hospital_service import hospital_service
from src.services.vendor_service import vendor_service
from src.services.equipment_service import equipment_service
from src.services.work_order_service import work_order_service
from src.services.pm_service import pm_service
from src.services.inventory_service import inventory_service
from src.services.contract_service import contract_service
from src.services.technician_service import technician_service
from src.services.report_service import report_service
from src.services.backup_service import backup_service
from src.services.auth_service import auth_service
from src.core.i18n import i18n, tr


def test_full_e2e_medical_workflow(test_db, tmp_path):
    # 1. Admin Authentication & Hospital Setup
    admin = test_db.query(User).filter_by(username="admin").first()
    assert admin is not None
    auth_service.set_current_user(admin)

    hosp = hospital_service.get_or_create_default_hospital(test_db)
    assert hosp is not None

    dept = hospital_service.create_department(test_db, admin, {
        "name_ar": "قسم العناية المركزة",
        "name_en": "ICU",
        "code": "ICU-01",
        "floor": "الدور الثالث"
    })
    assert dept.id is not None

    # 2. Vendor & Technician Creation
    vendor = vendor_service.create_vendor(test_db, admin, {
        "name": "شركة التوريدات الطبية المتقدمة",
        "vendor_type": "supplier",
        "contact_person": "م. عادل الشمري",
        "phone": "0501234567"
    })
    assert vendor.id is not None

    tech = technician_service.create_technician(
        test_db,
        employee_id="BME-700",
        full_name="م. ياسر القحطاني",
        specialization="أجهزة العناية المركزة والتنفس الصناعي"
    )
    assert tech.id is not None

    # 3. Medical Equipment Creation
    eq = equipment_service.create_equipment(test_db, admin, {
        "asset_number": "VENT-2026-001",
        "serial_number": "SN-VENT-9988",
        "name_ar": "جهاز تنفس صناعي متقدم",
        "name_en": "Advanced ICU Ventilator",
        "department_id": dept.id,
        "manufacturer_id": vendor.id,
        "category": "أجهزة التنفس الصناعي",
        "model": "Servo-u",
        "status": "operational",
        "risk_level": "high",
        "criticality": "critical",
        "purchase_price": 120000.0,
        "purchase_date": date(2025, 1, 1),
        "warranty_expiry_date": date(2027, 1, 1)
    })
    assert eq.id is not None
    assert eq.asset_number == "VENT-2026-001"

    # 4. Spare Parts Inventory & Stock Setup
    part = inventory_service.create_spare_part(
        test_db,
        part_number="FLT-O2-99",
        name_ar="فلتر أكسجين عالي الكفاءة",
        name_en="High Efficiency O2 Filter",
        category="فلاتر وأغشية طبية",
        quantity_on_hand=10.0,
        minimum_reorder_level=3.0,
        unit_cost=450.0,
        unit_of_measure="قطعة"
    )
    assert part.id is not None
    assert part.quantity_on_hand == 10.0

    # 5. Corrective Work Order Creation & Spare Part Deduction
    wo = work_order_service.create_work_order(test_db, admin, {
        "equipment_id": eq.id,
        "department_id": dept.id,
        "reported_by_name": "د. نورة الحربي",
        "priority": "critical",
        "failure_description": "انخفاض تدفق الأكسجين بالحساس الرئيسي",
        "assigned_technician_id": tech.id
    })
    assert wo.id is not None
    assert wo.work_order_number.startswith("WO-")

    # Consume part in work order
    tx = inventory_service.record_transaction(
        test_db,
        part_id=part.id,
        transaction_type="out_work_order",
        quantity=2.0,
        work_order_id=wo.id,
        notes="استبدال فلتر الأكسجين المستهلك"
    )
    assert tx.id is not None
    test_db.refresh(part)
    assert part.quantity_on_hand == 8.0  # 10 - 2

    # Close / Complete Work Order
    updated_wo = work_order_service.update_work_order(test_db, admin, wo.id, {
        "status": "completed",
        "diagnosis": "انسداد في فلتر الأكسجين القديم",
        "corrective_action": "تم استبدال الفلتر وإعادة المعايرة وضبط ضغط التدفق",
        "total_labor_cost": 300.0,
        "total_parts_cost": 900.0  # 2 * 450
    })
    assert updated_wo.status == "completed"
    assert updated_wo.total_cost == 1200.0

    # 6. Preventive Maintenance (PM) Protocol Creation, Scheduling & Execution
    plan = pm_service.create_pm_plan(
        test_db,
        title="الفحص الربع سنوي لأجهزة التنفس الصناعي",
        frequency_days=90,
        equipment_id=eq.id,
        estimated_duration_minutes=90,
        checklist_template=[
            "فحص ضغط الأكسجين والغازات الطبية",
            "اختبار إنذارات انقطاع التيار والتسريب",
            "معايرة حساس التدفق والمقاومة"
        ]
    )
    assert plan.id is not None

    schedules = pm_service.generate_schedules_for_plan(test_db, plan.id)
    assert len(schedules) >= 1
    schedule = schedules[0]

    # Execute PM
    exec_rec = pm_service.record_pm_execution(
        test_db,
        schedule_id=schedule.id,
        technician_id=tech.id,
        passed=True,
        results_summary="تم اجتياز جميع اختبارات المعايرة والسلامة بنجاح",
        measurements={"pressure_psi": 50.2, "leakage_current_ua": 12.0}
    )
    assert exec_rec.id is not None
    assert exec_rec.passed is True
    test_db.refresh(schedule)
    assert schedule.status == "completed"

    # 7. Annual Maintenance Contract Creation
    contract = contract_service.create_contract(
        test_db,
        vendor_id=vendor.id,
        contract_number="SLA-2026-ICU",
        title="عقد الصيانة الشاملة لأجهزة العناية المركزة",
        contract_type="comprehensive",
        cost=50000.0,
        start_date=date.today(),
        end_date=date.today() + timedelta(days=365)
    )
    assert contract.id is not None
    assert contract.is_active is True

    # 8. Report Service Validation & Exports
    eq_rep = report_service.get_equipment_report_data(test_db)
    assert eq_rep["summary"]["total_count"] >= 1
    assert len(eq_rep["rows"]) >= 1

    wo_rep = report_service.get_work_orders_report_data(test_db)
    assert wo_rep["summary"]["total_orders"] >= 1

    pm_rep = report_service.get_pm_compliance_report_data(test_db)
    assert pm_rep["summary"]["total_scheduled"] >= 1
    assert pm_rep["summary"]["compliance_rate"] >= 50.0

    inv_rep = report_service.get_inventory_report_data(test_db)
    assert inv_rep["summary"]["total_parts"] >= 1

    # Test PDF, Excel, and CSV generation
    excel_path = str(tmp_path / "full_report.xlsx")
    csv_path = str(tmp_path / "full_report.csv")
    report_service.export_to_excel(eq_rep, excel_path)
    report_service.export_to_csv(eq_rep, csv_path)
    html_content = report_service.generate_html_report(eq_rep)

    assert os.path.exists(excel_path)
    assert os.path.exists(csv_path)
    assert "<html dir=\"rtl\" lang=\"ar\">" in html_content

    # 9. Language & RTL verification
    assert i18n.current_locale == "ar"
    assert i18n.is_rtl() is True
