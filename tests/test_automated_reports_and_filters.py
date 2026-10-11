"""
Automated unit & integration tests for MEMMS Reports Suite and Monthly Engine:
- Section 6: Comprehensive Reporting Suite (Manufacturer, Vendor/Agent, Category, Department, Warranty, Periodic)
- Section 7: Export formats (Excel, CSV, HTML/PDF)
- Section 8: Automated Monthly Reports Engine, Startup Catch-up & Duplicate Prevention
"""
import pytest
import os
from datetime import date, datetime
from pathlib import Path

from src.models import (
    User, Role, Equipment, Vendor, VendorEngineer, Department, Hospital,
    WorkOrder, PMSchedule, PMPlan, SparePart, GeneratedReport
)
from src.services.report_service import report_service
from src.services.monthly_report_service import monthly_report_service


def _seed_report_environment(db):
    hosp = db.query(Hospital).first()
    if not hosp:
        hosp = Hospital(name_ar="مستشفى الملك فهد", name_en="KFSH", code="KFSH-01")
        db.add(hosp)
        db.commit()

    dept = db.query(Department).first()
    if not dept:
        dept = Department(hospital_id=hosp.id, name_ar="قسم القلب", name_en="Cardiology", code="CARD")
        db.add(dept)
        db.commit()

    vendor = db.query(Vendor).first()
    if not vendor:
        vendor = Vendor(name="شركة الدواء والمعدات", vendor_type="manufacturer", phone="0112224444")
        db.add(vendor)
        db.commit()

    eq1 = Equipment(
        asset_number="EQ-REP-001",
        serial_number="SN-REP-001",
        name_ar="تخطيط قلب متقدم",
        name_en="ECG Monitor",
        model="CardioTouch 3000",
        category="Monitoring",
        department_id=dept.id,
        manufacturer_id=vendor.id,
        agent_id=vendor.id,
        status="operational",
        risk_level="high",
        purchase_price=25000.0,
        warranty_expiry_date=date(2027, 6, 1)
    )
    eq2 = Equipment(
        asset_number="EQ-REP-002",
        serial_number="SN-REP-002",
        name_ar="صادم كهربائي للقلب",
        name_en="Defibrillator",
        model="Lifepak 20",
        category="Therapeutic",
        department_id=dept.id,
        manufacturer_id=vendor.id,
        status="under_maintenance",
        risk_level="high",
        purchase_price=40000.0,
        warranty_expiry_date=date(2025, 1, 1)  # expired
    )
    db.add_all([eq1, eq2])
    db.commit()

    wo = WorkOrder(
        work_order_number="WO-2026-9001",
        equipment_id=eq2.id,
        department_id=dept.id,
        reported_by_name="د. محمد",
        priority="high",
        status="completed",
        report_date=datetime(2026, 2, 10, 9, 30),
        completed_at=datetime(2026, 2, 11, 14, 0),
        total_labor_cost=1500.0,
        total_parts_cost=2000.0,
        failure_description="عطل في تفريغ شحنة الصدمة الكهربائية"
    )
    db.add(wo)
    db.commit()

    return {
        "hospital": hosp,
        "department": dept,
        "vendor": vendor,
        "equipment": [eq1, eq2],
        "work_order": wo
    }


def test_manufacturer_and_vendor_reports(test_db):
    """Test manufacturer and vendor/agent queries and aggregation."""
    env = _seed_report_environment(test_db)
    vendor_id = env["vendor"].id

    # 1. Manufacturer Report
    manuf_data = report_service.get_manufacturer_report_data(test_db, manufacturer_id=vendor_id)
    assert manuf_data["title"] == "تقرير الأجهزة الطبية حسب الشركة المصنعة"
    assert len(manuf_data["rows"]) == 2
    assert manuf_data["summary"]["total_count"] == 2
    assert manuf_data["summary"]["operational_count"] == 1
    assert manuf_data["summary"]["under_warranty"] == 1
    assert manuf_data["summary"]["total_value"] == 65000.0

    # 2. Vendor & Agent Report
    vendor_data = report_service.get_vendor_agent_report_data(test_db, vendor_id=vendor_id)
    assert vendor_data["title"] == "تقرير الأجهزة المرتبطة بالوكلاء والموردين"
    assert len(vendor_data["rows"]) >= 1


def test_category_department_and_warranty_reports(test_db):
    """Test category, department summary, and warranty expiration reports."""
    env = _seed_report_environment(test_db)
    dept_id = env["department"].id

    # 1. Category Report
    cat_data = report_service.get_category_report_data(test_db, category="Therapeutic")
    assert cat_data["summary"]["total_count"] == 1
    assert cat_data["rows"][0]["name_ar"] == "صادم كهربائي للقلب"

    # 2. Department Summary Report
    dept_data = report_service.get_department_report_data(test_db, department_id=dept_id)
    assert dept_data["summary"]["grand_total"] == 2
    assert dept_data["summary"]["grand_operational"] == 1
    assert dept_data["summary"]["grand_down"] == 1

    # 3. Warranty Report (expired)
    w_expired = report_service.get_warranty_report_data(test_db, warranty_filter="expired")
    assert w_expired["summary"]["total_count"] >= 1
    assert any(r["asset_number"] == "EQ-REP-002" for r in w_expired["rows"])

    # 4. Periodic Maintenance & Cost Report
    pm_data = report_service.get_periodic_maintenance_report_data(test_db)
    assert pm_data["summary"]["total_orders"] >= 1
    assert pm_data["summary"]["total_cost"] == 3500.0


def test_report_export_excel_csv_and_html(test_db, tmp_path):
    """Test export pipelines for Excel (.xlsx), CSV (.csv), and localized HTML."""
    env = _seed_report_environment(test_db)
    data = report_service.get_equipment_report_data(test_db)

    # 1. Excel Export
    excel_path = tmp_path / "test_report.xlsx"
    report_service.export_to_excel(data, str(excel_path))
    assert excel_path.exists()
    assert excel_path.stat().st_size > 0

    # 2. CSV Export
    csv_path = tmp_path / "test_report.csv"
    report_service.export_to_csv(data, str(csv_path))
    assert csv_path.exists()
    assert csv_path.stat().st_size > 0

    # 3. HTML Generation for PDF
    html = report_service.generate_html_report(data)
    assert "dir=\"rtl\"" in html or "dir='rtl'" in html
    assert "تقرير" in html
    assert "EQ-REP-001" in html


def test_monthly_report_engine_and_catchup(test_db, tmp_path):
    """Test automated monthly reports generation, duplicate prevention, and archive history."""
    _seed_report_environment(test_db)
    admin = test_db.query(User).filter_by(username="admin").first()

    # Override report directory to isolated temp path for test
    monthly_report_service.reports_dir = tmp_path / "monthly_reports"
    monthly_report_service.reports_dir.mkdir(parents=True, exist_ok=True)

    # 1. Generate monthly reports for 2026/02
    results = monthly_report_service.generate_all_monthly_reports(
        db=test_db,
        year=2026,
        month=2,
        user=admin
    )
    failures = [(r.report_type, r.status, r.error_message) for r in results if r.status != "success"]
    assert not failures, f"Failed reports: {failures}"

    # Verify generated files on disk
    period_folder = monthly_report_service.reports_dir / "2026_02"
    assert period_folder.exists()
    pdf_files = list(period_folder.glob("*.pdf"))
    excel_files = list(period_folder.glob("*.xlsx"))
    assert len(pdf_files) == 7
    assert len(excel_files) == 7

    # 2. Duplicate Prevention: running again without force should return existing
    second_run = monthly_report_service.generate_all_monthly_reports(
        db=test_db,
        year=2026,
        month=2,
        user=admin,
        force=False
    )
    assert len(second_run) == 7
    assert [r.id for r in second_run] == [r.id for r in results]

    # 3. Query History
    history = monthly_report_service.get_generated_reports_history(test_db, year=2026, month=2)
    assert len(history) == 7

    # 4. Startup Catch-up runner
    monthly_report_service.check_and_run_startup_catchup(test_db)
