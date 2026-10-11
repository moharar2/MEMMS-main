"""
Automated Monthly Reports Engine for MEMMS.
Generates, formats, archives, and tracks monthly medical equipment maintenance reports.
Supports startup catch-up execution, non-blocking generation, and duplicate prevention.
"""
import os
import calendar
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_

import config
from src.core.database import get_db
from src.models.report import GeneratedReport
from src.models.equipment import Equipment
from src.models.work_order import WorkOrder
from src.models.preventive import PMSchedule, PMExecution
from src.models.hospital import Department
from src.models.vendor import Vendor
from src.services.report_service import report_service
from src.services.audit_service import audit_service


class MonthlyReportService:
    REPORT_DEFINITIONS = [
        ("monthly_new_equipment", "تقرير الأجهزة المسجلة والمضافة خلال الشهر"),
        ("monthly_closed_work_orders", "تقرير أوامر العمل المنفذة والمغلقة والتكاليف"),
        ("monthly_pm_compliance", "تقرير الامتثال للصيانة الوقائية والمهام المنجزة والمتأخرة"),
        ("monthly_down_equipment", "تقرير الأجهزة المتوقفة وحالات الخروج عن الخدمة"),
        ("monthly_warranty_expiring", "تقرير الأجهزة التي انتهى ضمانها أو اقترب انتهاؤه"),
        ("monthly_department_summary", "تقرير ملخص الأعطال والصيانة بحسب الأقسام الطبية"),
        ("monthly_vendor_performance", "تقرير الأعمال المنفذة بواسطة الوكلاء والموردين")
    ]

    def __init__(self):
        self.reports_dir = config.DATA_DIR / "reports" / "monthly"
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def get_previous_month(ref_date: Optional[date] = None) -> Tuple[int, int]:
        """Returns (year, month) of the previous calendar month."""
        ref = ref_date or date.today()
        first_day_current = date(ref.year, ref.month, 1)
        last_day_prev = first_day_current - timedelta(days=1)
        return last_day_prev.year, last_day_prev.month

    @staticmethod
    def get_month_date_range(year: int, month: int) -> Tuple[date, date]:
        """Returns (start_date, end_date) for a given month and year."""
        _, last_day = calendar.monthrange(year, month)
        return date(year, month, 1), date(year, month, last_day)

    def generate_all_monthly_reports(
        self,
        db: Session,
        year: int,
        month: int,
        user=None,
        force: bool = False
    ) -> List[GeneratedReport]:
        """Generates all 7 monthly reports for the specified period."""
        results = []
        for r_type, title in self.REPORT_DEFINITIONS:
            rep = self.generate_single_monthly_report(
                db=db,
                report_type=r_type,
                year=year,
                month=month,
                user=user,
                force=force
            )
            results.append(rep)
        return results

    def generate_single_monthly_report(
        self,
        db: Session,
        report_type: str,
        year: int,
        month: int,
        user=None,
        force: bool = False
    ) -> GeneratedReport:
        # Check if already generated
        existing = db.query(GeneratedReport).filter_by(
            report_type=report_type,
            period_year=year,
            period_month=month
        ).first()

        if existing and existing.status == "success" and not force:
            return existing

        period_folder = self.reports_dir / f"{year}_{month:02d}"
        period_folder.mkdir(parents=True, exist_ok=True)

        title_dict = dict(self.REPORT_DEFINITIONS)
        report_title = title_dict.get(report_type, "تقرير شهري")

        rep = existing or GeneratedReport(
            report_type=report_type,
            period_year=year,
            period_month=month,
            title=f"{report_title} — {year}/{month:02d}",
            generated_by_user_id=user.id if user else None
        )
        if not existing:
            db.add(rep)

        start_date, end_date = self.get_month_date_range(year, month)

        try:
            report_data = self._build_report_data(db, report_type, start_date, end_date, year, month)

            # Export files
            pdf_path = period_folder / f"{report_type}_{year}_{month:02d}.pdf"
            excel_path = period_folder / f"{report_type}_{year}_{month:02d}.xlsx"

            # 1. PDF / Printable document
            html_content = report_service.generate_html_report(report_data)
            try:
                from PySide6.QtWidgets import QApplication
                from PySide6.QtGui import QTextDocument, QPdfWriter, QPageSize, QPageLayout, QFont
                from PySide6.QtCore import QSizeF, QMarginsF

                _app = QApplication.instance() or QApplication([])
                writer = QPdfWriter(str(pdf_path))
                writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
                orientation = report_service.get_page_orientation(report_data)
                writer.setPageOrientation(
                    QPageLayout.Orientation.Landscape if orientation == "landscape"
                    else QPageLayout.Orientation.Portrait
                )
                writer.setPageMargins(QMarginsF(10, 10, 10, 10), QPageLayout.Unit.Millimeter)
                writer.setResolution(96)

                doc = QTextDocument()
                paint_rect = writer.pageLayout().paintRectPixels(writer.resolution())
                doc.setPageSize(QSizeF(paint_rect.width(), paint_rect.height()))
                report_service.prepare_rtl_document(doc, html_content, font_size=10)
                doc.print_(writer)
                del doc
                del writer
                import gc
                gc.collect()
                _app.processEvents()
            except Exception as pdf_err:
                # Fallback to HTML if PDF writer cannot initialize
                pdf_path = period_folder / f"{report_type}_{year}_{month:02d}.html"
                with open(pdf_path, "w", encoding="utf-8") as f:
                    f.write(html_content)

            # 2. Excel version
            report_service.export_to_excel(report_data, str(excel_path))

            rep.file_path_pdf = str(pdf_path)
            rep.file_path_excel = str(excel_path)
            rep.status = "success"
            rep.error_message = None
            rep.generated_at = datetime.now()

            audit_service.log_action(
                db=db,
                user=user,
                action="GENERATE_MONTHLY_REPORT",
                entity_name="GeneratedReport",
                entity_id=str(rep.id or 0),
                details=f"توليد التقرير الشهري: {rep.title}"
            )

        except Exception as e:
            rep.status = "failed"
            rep.error_message = str(e)

        db.commit()
        db.refresh(rep)
        return rep

    def _build_report_data(
        self,
        db: Session,
        report_type: str,
        start_date: date,
        end_date: date,
        year: int,
        month: int
    ) -> Dict[str, Any]:
        """Builds specific report data payload according to report type."""
        month_label = f"{year}/{month:02d}"

        if report_type == "monthly_new_equipment":
            # Devices added or installed during the month
            query = db.query(Equipment).filter(
                or_(
                    and_(Equipment.installation_date >= start_date, Equipment.installation_date <= end_date),
                    and_(Equipment.created_at >= datetime.combine(start_date, datetime.min.time()),
                         Equipment.created_at <= datetime.combine(end_date, datetime.max.time()))
                )
            )
            items = query.order_by(Equipment.id.desc()).all()
            column_keys = ["asset_number", "name_ar", "model", "serial_number", "department", "category", "purchase_price"]
            rows = []
            for eq in items:
                rows.append({
                    "id": eq.id,
                    "asset_number": eq.asset_number or "-",
                    "name_ar": eq.name_ar or "-",
                    "model": eq.model or "-",
                    "serial_number": eq.serial_number or "-",
                    "department": eq.department.name_ar if eq.department else "-",
                    "category": eq.category or "-",
                    "purchase_price": float(eq.purchase_price or 0.0)
                })
            return {
                "title": f"تقرير الأجهزة المسجلة والمضافة خلال شهر ({month_label})",
                "column_keys": column_keys,
                "summary": {
                    "total_count": len(items),
                    "total_value": sum(float(e.purchase_price or 0.0) for e in items),
                    "display": {
                        "إجمالي الأجهزة المضافة": len(items),
                        "إجمالي القيمة التقديرية": f"{sum(float(e.purchase_price or 0.0) for e in items):,.2f} ر.س"
                    }
                },
                "headers": ["رقم الأصل", "اسم الجهاز", "الموديل", "الرقم التسلسلي", "القسم", "التصنيف", "سعر الشراء"],
                "rows": rows
            }

        elif report_type == "monthly_closed_work_orders":
            query = db.query(WorkOrder).filter(
                WorkOrder.completed_at >= datetime.combine(start_date, datetime.min.time()),
                WorkOrder.completed_at <= datetime.combine(end_date, datetime.max.time()),
                WorkOrder.status.in_(("completed", "closed"))
            )
            items = query.order_by(WorkOrder.completed_at.desc()).all()
            column_keys = ["work_order_number", "equipment", "department", "technician", "completed_date", "total_cost"]
            rows = []
            for wo in items:
                eq_name = f"{wo.equipment.name_ar} ({wo.equipment.asset_number})" if wo.equipment else "-"
                dept_name = wo.equipment.department.name_ar if (wo.equipment and wo.equipment.department) else "-"
                rows.append({
                    "id": wo.id,
                    "work_order_number": wo.work_order_number,
                    "equipment": eq_name,
                    "department": dept_name,
                    "technician": wo.assigned_technician.full_name if wo.assigned_technician else "-",
                    "completed_date": wo.completed_at.strftime("%Y-%m-%d") if wo.completed_at else "-",
                    "total_cost": float(wo.total_cost or 0.0)
                })
            total_cost = sum(float(w.total_cost or 0.0) for w in items)
            return {
                "title": f"تقرير أوامر العمل المنجزة والمغلقة خلال شهر ({month_label})",
                "column_keys": column_keys,
                "summary": {
                    "closed_orders": len(items),
                    "total_cost": total_cost,
                    "display": {
                        "أوامر العمل المغلقة": len(items),
                        "إجمالي تكلفة الصيانة": f"{total_cost:,.2f} ر.س"
                    }
                },
                "headers": ["رقم أمر العمل", "الجهاز الطبي", "القسم", "الفني المسؤول", "تاريخ الإنجاز", "إجمالي التكلفة"],
                "rows": rows
            }

        elif report_type == "monthly_pm_compliance":
            return report_service.get_pm_compliance_report_data(
                db,
                from_date=start_date,
                to_date=end_date
            )

        elif report_type == "monthly_down_equipment":
            query = db.query(Equipment).filter(
                Equipment.status.in_(("under_maintenance", "out_of_service", "scrapped"))
            )
            items = query.order_by(Equipment.id.desc()).all()
            column_keys = ["asset_number", "name_ar", "model", "serial_number", "department", "status", "risk_level", "notes"]
            rows = []
            for eq in items:
                rows.append({
                    "id": eq.id,
                    "asset_number": eq.asset_number or "-",
                    "name_ar": eq.name_ar or "-",
                    "model": eq.model or "-",
                    "serial_number": eq.serial_number or "-",
                    "department": eq.department.name_ar if eq.department else "-",
                    "status": eq.status,
                    "risk_level": eq.risk_level,
                    "notes": eq.notes or "-"
                })
            return {
                "title": f"تقرير الأجهزة المتوقفة وخارج الخدمة لشهر ({month_label})",
                "column_keys": column_keys,
                "summary": {
                    "down_count": len(items),
                    "display": {"إجمالي الأجهزة المتوقفة": len(items)}
                },
                "headers": ["رقم الأصل", "اسم الجهاز", "الموديل", "الرقم التسلسلي", "القسم", "الحالة", "الخطورة", "ملاحظات"],
                "rows": rows
            }

        elif report_type == "monthly_warranty_expiring":
            return report_service.get_warranty_report_data(
                db,
                warranty_filter="expiring_soon",
                days_threshold=60
            )

        elif report_type == "monthly_department_summary":
            return report_service.get_department_report_data(db)

        elif report_type == "monthly_vendor_performance":
            return report_service.get_vendor_agent_report_data(
                db,
                from_date=start_date,
                to_date=end_date
            )

        else:
            return report_service.get_equipment_report_data(db)

    def check_and_run_startup_catchup(self, db: Session):
        """
        Executed on application startup.
        Checks if the previous month's reports have been generated; if missing, triggers generation.
        """
        prev_year, prev_month = self.get_previous_month()
        count = db.query(GeneratedReport).filter_by(
            period_year=prev_year,
            period_month=prev_month,
            status="success"
        ).count()

        if count < len(self.REPORT_DEFINITIONS):
            print(f"[MEMMS Report Engine] Running automated monthly reports catch-up for {prev_year}/{prev_month:02d}...")
            self.generate_all_monthly_reports(db, prev_year, prev_month)
            print("[MEMMS Report Engine] Monthly catch-up completed successfully.")

    def get_generated_reports_history(
        self,
        db: Session,
        year: Optional[int] = None,
        month: Optional[int] = None
    ) -> List[GeneratedReport]:
        """Retrieves list of generated reports archive."""
        query = db.query(GeneratedReport)
        if year:
            query = query.filter(GeneratedReport.period_year == year)
        if month:
            query = query.filter(GeneratedReport.period_month == month)
        return query.order_by(GeneratedReport.period_year.desc(), GeneratedReport.period_month.desc(), GeneratedReport.id.desc()).all()


monthly_report_service = MonthlyReportService()
