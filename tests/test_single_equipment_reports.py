"""
Unit tests for Single Equipment Maintenance Report (Passport) and Work Order Ticket export.
"""
import pytest
from src.core.database import get_db
from src.models.equipment import Equipment
from src.models.work_order import WorkOrder
from src.services.report_service import report_service


def test_equipment_history_report():
    with get_db() as db:
        eq = db.query(Equipment).first()
        assert eq is not None, "At least one equipment should exist in seed db"

        data = report_service.get_equipment_history_report_data(db, eq.id)
        assert data.get("is_single_equipment") is True
        assert data.get("equipment")["asset_number"] == eq.asset_number
        assert "work_orders" in data
        assert "pm_schedules" in data
        assert "parts_consumed" in data
        assert "summary" in data

        # Test HTML generation and RTL
        html = report_service.generate_equipment_history_html(data)
        assert "هيئة مستشفى الثورة العام النموذجي" in html
        assert eq.asset_number in html
        assert "بطاقة السجل الفني وتاريخ صيانة الجهاز الطبي" in html
        assert "توقيع" in html
        assert '<html dir="rtl" lang="ar">' in html
        assert "direction: rtl" in html
        assert 'dir="rtl"' in html


def test_work_order_ticket_report():
    with get_db() as db:
        wo = db.query(WorkOrder).first()
        assert wo is not None, "At least one work order should exist in seed db"

        data = report_service.get_work_order_ticket_data(db, wo.id)
        assert data.get("is_work_order_ticket") is True
        assert data.get("work_order")["number"] == wo.work_order_number
        assert "equipment" in data
        assert "parts" in data

        # Test HTML generation and RTL
        html = report_service.generate_work_order_ticket_html(data)
        assert "هيئة مستشفى الثورة العام النموذجي" in html
        assert wo.work_order_number in html
        assert "إشعار وتذكرة أمر صيانة طبية" in html
        assert "توقيع" in html
        assert '<html dir="rtl" lang="ar">' in html
        assert "direction: rtl" in html
        assert 'dir="rtl"' in html


def test_report_templates_share_a4_rtl_layout_and_escape_values():
    ticket = {
        "is_work_order_ticket": True,
        "work_order": {"number": "WO-RTL-01", "failure_description": "<sensor> & cable"},
        "equipment": {},
        "parts": []
    }
    ticket_html = report_service.generate_work_order_ticket_html(ticket)
    assert '<html dir="rtl" lang="ar">' in ticket_html
    assert "@page { size: A4 portrait;" in ticket_html
    assert "&lt;sensor&gt; &amp; cable" in ticket_html
    assert report_service.get_page_orientation(ticket) == "portrait"

    wide_report = {"headers": ["A", "B", "C", "D", "E", "F", "G", "H"]}
    assert report_service.get_page_orientation(wide_report) == "landscape"
    assert report_service.get_page_orientation({"headers": ["A", "B"]}) == "portrait"



def test_receiving_report_uses_shared_arabic_rtl_template():
    html = report_service.generate_receiving_report_html({
        "equipment": {"name_ar": "جهاز اختبار", "asset_number": "EQ-RTL-01"},
        "receiving": {"receipt_notes": "<ملاحظة> & بيانات"}
    })
    assert '<html dir="rtl" lang="ar">' in html
    assert "محضر استلام وتعميد جهاز طبي" in html
    assert "@page { size: A4 portrait;" in html
    assert "&lt;ملاحظة&gt; &amp; بيانات" in html
    assert "توقيع" in html



def test_reports_rtl_layout(tmp_path):
    with get_db() as db:
        eq_data = report_service.get_equipment_report_data(db)
        html = report_service.generate_html_report(eq_data)
        assert '<html dir="rtl" lang="ar">' in html
        assert "direction: rtl" in html
        assert '<table dir="rtl"' in html

        # Test Excel RTL export
        excel_path = tmp_path / "test_rtl.xlsx"
        report_service.export_to_excel(eq_data, str(excel_path))
        import openpyxl
        wb = openpyxl.load_workbook(str(excel_path))
        ws = wb.active
        assert ws.sheet_view.rightToLeft is True

        # Test prepare_rtl_document
        from PySide6.QtWidgets import QApplication
        from PySide6.QtGui import QTextDocument
        from PySide6.QtCore import Qt
        app = QApplication.instance() or QApplication([])
        doc = QTextDocument()
        report_service.prepare_rtl_document(doc, html)
        assert doc.defaultTextOption().textDirection() == Qt.LayoutDirection.RightToLeft

