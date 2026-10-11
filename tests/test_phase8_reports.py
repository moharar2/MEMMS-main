"""
Phase 8 Tests: Reports Service, Aggregations, and Export Functions.
"""
import os
import pytest
from datetime import date, datetime
from src.core.database import get_db
from src.models.equipment import Equipment
from src.models.work_order import WorkOrder
from src.models.preventive import PMPlan, PMExecution
from src.models.inventory import SparePart
from src.models.hospital import Department
from src.services.report_service import report_service


def test_equipment_report_data(test_db):
    data = report_service.get_equipment_report_data(test_db)
    assert "summary" in data
    assert "headers" in data
    assert "rows" in data
    assert data["summary"]["total_count"] >= 0
    assert "operational_count" in data["summary"]
    assert "total_value" in data["summary"]


def test_work_orders_report_data(test_db):
    data = report_service.get_work_orders_report_data(test_db)
    assert "summary" in data
    assert "headers" in data
    assert "rows" in data
    assert "total_orders" in data["summary"]
    assert "total_cost" in data["summary"]


def test_pm_compliance_report_data(test_db):
    data = report_service.get_pm_compliance_report_data(test_db)
    assert "summary" in data
    assert "headers" in data
    assert "rows" in data
    assert "compliance_rate" in data["summary"]


def test_inventory_report_data(test_db):
    data = report_service.get_inventory_report_data(test_db)
    assert "summary" in data
    assert "headers" in data
    assert "rows" in data
    assert "total_valuation" in data["summary"]


def test_report_exports_excel_and_csv(test_db, tmp_path):
    data = report_service.get_equipment_report_data(test_db)
    
    # Test CSV
    csv_file = str(tmp_path / "equipment_report.csv")
    report_service.export_to_csv(data, csv_file)
    assert os.path.exists(csv_file)
    assert os.path.getsize(csv_file) > 0

    # Test Excel
    xlsx_file = str(tmp_path / "equipment_report.xlsx")
    report_service.export_to_excel(data, xlsx_file)
    assert os.path.exists(xlsx_file)
    assert os.path.getsize(xlsx_file) > 0

    # Test HTML Document generation
    html = report_service.generate_html_report(data)
    assert "<html" in html.lower()
    assert "MEMMS" in html
