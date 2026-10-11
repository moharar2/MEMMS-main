"""
Enterprise Report & Analytics Service.
Generates comprehensive reports, statistical aggregations, and exports (Excel, CSV, PDF/HTML).
Fully localized, explicit column mapping, zero emojis.
"""
import io
import csv
import re
from html import escape as html_escape
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_

from src.models.equipment import Equipment, EquipmentTransfer
from src.models.work_order import WorkOrder, WorkOrderPart
from src.models.preventive import PMPlan, PMSchedule, PMExecution
from src.models.inventory import SparePart, InventoryTransaction
from src.models.hospital import Department, Hospital
from src.models.technician import Technician
from src.models.vendor import Vendor
from src.core.i18n import tr


class ReportService:
    # ── 1. Equipment Inventory Report ────────────────────────────────────────
    def get_equipment_report_data(
        self,
        db: Session,
        department_id: Optional[int] = None,
        status: Optional[str] = None,
        risk_level: Optional[str] = None,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        query = db.query(Equipment)
        if department_id:
            query = query.filter(Equipment.department_id == department_id)
        if status and status != "all":
            query = query.filter(Equipment.status == status)
        if risk_level and risk_level != "all":
            query = query.filter(Equipment.risk_level == risk_level)
        if category and category != "all":
            query = query.filter(Equipment.category == category)

        items = query.order_by(Equipment.id.desc()).all()

        total_count = len(items)
        operational_count = sum(1 for e in items if e.status == "operational")
        in_maintenance = sum(1 for e in items if e.status == "under_maintenance")
        out_of_service = sum(1 for e in items if e.status == "out_of_service")
        total_value = sum(float(e.purchase_price or 0.0) for e in items)

        column_keys = [
            "asset_number", "name_ar", "model", "serial_number", "department",
            "category", "status", "risk_level", "purchase_price", "warranty_expiry"
        ]

        rows = []
        for eq in items:
            dept_name = eq.department.name_ar if eq.department else "-"
            status_text = tr(f"status.{eq.status}", default=eq.status)
            risk_text = tr(f"risk.{eq.risk_level}", default=eq.risk_level)

            rows.append({
                "id": eq.id,
                "asset_number": eq.asset_number or "-",
                "name_ar": eq.name_ar or "-",
                "model": eq.model or "-",
                "serial_number": eq.serial_number or "-",
                "department": dept_name,
                "category": eq.category or "-",
                "status": status_text,
                "risk_level": risk_text,
                "purchase_price": float(eq.purchase_price or 0.0),
                "purchase_date": eq.purchase_date.strftime("%Y-%m-%d") if eq.purchase_date else "-",
                "warranty_expiry": eq.warranty_expiry_date.strftime("%Y-%m-%d") if eq.warranty_expiry_date else "-",
            })

        return {
            "title": tr("reports.equipment_inventory_report"),
            "column_keys": column_keys,
            "summary": {
                "total_count": total_count,
                "operational_count": operational_count,
                "in_maintenance": in_maintenance,
                "out_of_service": out_of_service,
                "total_value": total_value,
                "display": {
                    "إجمالي الأجهزة": total_count,
                    "الأجهزة العاملة": operational_count,
                    "تحت الصيانة": in_maintenance,
                    "خارج الخدمة": out_of_service,
                    "القيمة الإجمالية للأصول": f"{total_value:,.2f} ر.س"
                }
            },
            "headers": [
                tr("equipment.asset_id"),
                tr("equipment.name_ar"),
                tr("equipment.model"),
                tr("equipment.serial_number"),
                tr("equipment.department"),
                tr("equipment.category"),
                tr("equipment.status"),
                tr("equipment.risk_level"),
                tr("equipment.purchase_price"),
                tr("equipment.warranty_expiry")
            ],
            "rows": rows
        }

    # ── 2. Work Orders Report ────────────────────────────────────────────────
    def get_work_orders_report_data(
        self,
        db: Session,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        department_id: Optional[int] = None
    ) -> Dict[str, Any]:
        query = db.query(WorkOrder)

        if from_date:
            query = query.filter(WorkOrder.created_at >= datetime.combine(from_date, datetime.min.time()))
        if to_date:
            query = query.filter(WorkOrder.created_at <= datetime.combine(to_date, datetime.max.time()))
        if status and status != "all":
            query = query.filter(WorkOrder.status == status)
        if priority and priority != "all":
            query = query.filter(WorkOrder.priority == priority)
        if department_id:
            query = query.join(Equipment).filter(Equipment.department_id == department_id)

        orders = query.order_by(WorkOrder.id.desc()).all()

        total_orders = len(orders)
        completed_count = sum(1 for o in orders if o.status in ("completed", "closed"))
        open_count = sum(1 for o in orders if o.status in ("open", "pending", "assigned"))
        in_progress = sum(1 for o in orders if o.status == "in_progress")
        total_cost = sum(float(o.total_cost or 0.0) for o in orders)
        parts_cost = sum(float(o.total_parts_cost or 0.0) for o in orders)
        labor_cost = sum(float(o.total_labor_cost or 0.0) for o in orders)

        column_keys = [
            "work_order_number", "equipment", "priority", "status", "reported_date",
            "technician", "failure_description", "completed_date", "parts_cost",
            "labor_cost", "total_cost"
        ]

        rows = []
        for o in orders:
            eq_name = f"{o.equipment.name_ar} ({o.equipment.asset_number})" if o.equipment else "-"
            tech_name = o.assigned_technician.full_name if o.assigned_technician else "-"
            created_str = o.created_at.strftime("%Y-%m-%d") if o.created_at else "-"
            completed_str = o.completed_at.strftime("%Y-%m-%d") if o.completed_at else "-"
            status_text = tr(f"status.{o.status}", default=o.status)
            priority_text = tr(f"priority.{o.priority}", default=o.priority)

            rows.append({
                "id": o.id,
                "work_order_number": o.work_order_number,
                "equipment": eq_name,
                "priority": priority_text,
                "status": status_text,
                "reported_date": created_str,
                "technician": tech_name,
                "failure_description": o.failure_description or "-",
                "completed_date": completed_str,
                "parts_cost": float(o.total_parts_cost or 0.0),
                "labor_cost": float(o.total_labor_cost or 0.0),
                "total_cost": float(o.total_cost or 0.0)
            })

        return {
            "title": tr("reports.work_orders_summary_report"),
            "column_keys": column_keys,
            "summary": {
                "total_orders": total_orders,
                "completed_count": completed_count,
                "open_count": open_count,
                "in_progress": in_progress,
                "parts_cost": parts_cost,
                "labor_cost": labor_cost,
                "total_cost": total_cost,
                "display": {
                    "إجمالي أوامر العمل": total_orders,
                    "الأوامر المكتملة": completed_count,
                    "الأوامر المفتوحة": open_count,
                    "قيد التنفيذ": in_progress,
                    "تكلفة قطع الغيار": f"{parts_cost:,.2f} ر.س",
                    "تكلفة العمالة": f"{labor_cost:,.2f} ر.س",
                    "التكلفة الإجمالية للصيانة": f"{total_cost:,.2f} ر.س"
                }
            },
            "headers": [
                tr("work_orders.order_number"),
                tr("work_orders.equipment"),
                tr("common.priority"),
                tr("common.status"),
                tr("work_orders.report_date"),
                tr("work_orders.assigned_to"),
                tr("work_orders.problem_description"),
                tr("work_orders.completed_at"),
                tr("work_orders.parts_cost"),
                tr("work_orders.labor_cost"),
                tr("work_orders.total_cost")
            ],
            "rows": rows
        }

    # ── 3. Preventive Maintenance Compliance Report ──────────────────────────
    def get_pm_compliance_report_data(
        self,
        db: Session,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        query = db.query(PMSchedule)

        if from_date:
            query = query.filter(PMSchedule.due_date >= from_date)
        if to_date:
            query = query.filter(PMSchedule.due_date <= to_date)
        if status and status != "all":
            query = query.filter(PMSchedule.status == status)

        schedules = query.order_by(PMSchedule.due_date.desc()).all()

        total_pm = len(schedules)
        completed_pm = sum(1 for p in schedules if p.status == "completed")
        pending_pm = sum(1 for p in schedules if p.status == "scheduled")
        overdue_pm = sum(1 for p in schedules if p.status == "overdue")
        compliance_rate = round((completed_pm / total_pm * 100), 1) if total_pm > 0 else 100.0

        column_keys = [
            "scheduled_date", "equipment", "plan_title", "status",
            "result", "technician", "executed_date", "notes"
        ]

        rows = []
        for s in schedules:
            plan_title = s.plan.title if s.plan else "-"
            eq_name = f"{s.equipment.name_ar} ({s.equipment.asset_number})" if s.equipment else "-"
            sched_str = s.due_date.strftime("%Y-%m-%d") if s.due_date else "-"
            status_text = tr(f"status.{s.status}", default=s.status)

            tech_name = "-"
            exec_str = "-"
            result_str = "-"
            notes_str = "-"
            if s.execution:
                tech_name = s.execution.technician.full_name if s.execution.technician else "-"
                exec_str = s.execution.execution_date.strftime("%Y-%m-%d") if s.execution.execution_date else "-"
                result_str = tr("pm.passed") if s.execution.passed else tr("pm.failed")
                notes_str = s.execution.results_summary or s.execution.notes or "-"

            rows.append({
                "id": s.id,
                "scheduled_date": sched_str,
                "equipment": eq_name,
                "plan_title": plan_title,
                "status": status_text,
                "result": result_str,
                "technician": tech_name,
                "executed_date": exec_str,
                "notes": notes_str
            })

        return {
            "title": tr("reports.pm_compliance_report"),
            "column_keys": column_keys,
            "summary": {
                "total_scheduled": total_pm,
                "completed_count": completed_pm,
                "pending_count": pending_pm,
                "overdue_count": overdue_pm,
                "compliance_rate": compliance_rate,
                "display": {
                    "إجمالي المهام المجدولة": total_pm,
                    "المهام المنجزة": completed_pm,
                    "المهام المعلقة": pending_pm,
                    "المهام المتأخرة": overdue_pm,
                    "نسبة الالتزام بالصيانة الوقائية": f"{compliance_rate}%"
                }
            },
            "headers": [
                tr("pm.scheduled_date"),
                tr("pm.equipment"),
                tr("pm.plan_title"),
                tr("common.status"),
                tr("pm.result"),
                tr("pm.performed_by"),
                tr("pm.execution_date"),
                tr("common.notes")
            ],
            "rows": rows
        }

    # ── 4. Inventory & Spare Parts Valuation Report ──────────────────────────
    def get_inventory_report_data(
        self,
        db: Session,
        category: Optional[str] = None,
        low_stock_only: bool = False
    ) -> Dict[str, Any]:
        query = db.query(SparePart).filter(SparePart.is_active.is_(True))

        if category and category != "all":
            query = query.filter(SparePart.category == category)
        if low_stock_only:
            query = query.filter(SparePart.quantity_on_hand <= SparePart.minimum_reorder_level)

        parts = query.order_by(SparePart.id.desc()).all()

        total_parts = len(parts)
        low_stock_count = sum(1 for p in parts if (p.quantity_on_hand or 0) <= (p.minimum_reorder_level or 0))
        total_valuation = sum(float(p.quantity_on_hand or 0) * float(p.unit_cost or 0.0) for p in parts)
        total_quantity = sum(float(p.quantity_on_hand or 0) for p in parts)

        column_keys = [
            "part_number", "name_ar", "category", "quantity", "min_quantity",
            "unit_price", "total_valuation", "location", "vendor"
        ]

        rows = []
        for p in parts:
            stock_qty = p.quantity_on_hand or 0
            unit_price = float(p.unit_cost or 0.0)
            total_cost = round(stock_qty * unit_price, 2)
            vendor_name = p.manufacturer.name if p.manufacturer else "-"

            rows.append({
                "id": p.id,
                "part_number": p.part_number or "-",
                "name_ar": p.name_ar or "-",
                "name_en": p.name_en or "-",
                "category": p.category or "-",
                "quantity": f"{stock_qty:g} {p.unit_of_measure or ''}",
                "min_quantity": f"{p.minimum_reorder_level or 0:g} {p.unit_of_measure or ''}",
                "unit_price": unit_price,
                "total_valuation": total_cost,
                "location": p.storage_bin_location or "-",
                "vendor": vendor_name,
                "is_low_stock": stock_qty <= (p.minimum_reorder_level or 0)
            })

        return {
            "title": tr("reports.inventory_valuation_report"),
            "column_keys": column_keys,
            "summary": {
                "total_parts": total_parts,
                "low_stock_count": low_stock_count,
                "total_quantity": total_quantity,
                "total_valuation": total_valuation,
                "display": {
                    "إجمالي أصناف قطع الغيار": total_parts,
                    "الأصناف منخفضة المخزون": low_stock_count,
                    "إجمالي الكميات بالمخزن": total_quantity,
                    "القيمة الإجمالية للمخزون": f"{total_valuation:,.2f} ر.س"
                }
            },
            "headers": [
                tr("inventory.part_number"),
                tr("inventory.name_ar"),
                tr("inventory.category"),
                tr("inventory.quantity"),
                tr("inventory.reorder_level"),
                tr("inventory.unit_cost"),
                tr("inventory.total_value"),
                tr("inventory.bin_location"),
                tr("inventory.manufacturer")
            ],
            "rows": rows
        }

    # ── 5. Manufacturer Report ───────────────────────────────────────────────
    def get_manufacturer_report_data(
        self,
        db: Session,
        manufacturer_id: Optional[int] = None,
        department_id: Optional[int] = None
    ) -> Dict[str, Any]:
        query = db.query(Equipment)
        if manufacturer_id and manufacturer_id != "all":
            query = query.filter(Equipment.manufacturer_id == manufacturer_id)
        if department_id:
            query = query.filter(Equipment.department_id == department_id)

        items = query.order_by(Equipment.manufacturer_id.asc(), Equipment.id.desc()).all()
        today = date.today()

        total_count = len(items)
        operational_count = sum(1 for e in items if e.status == "operational")
        under_warranty = sum(1 for e in items if e.warranty_expiry_date and e.warranty_expiry_date >= today)
        total_value = sum(float(e.purchase_price or 0.0) for e in items)

        column_keys = [
            "manufacturer", "asset_number", "name_ar", "model", "serial_number",
            "department", "warranty_status", "status", "purchase_price"
        ]

        rows = []
        for eq in items:
            manuf_name = eq.manufacturer.name if eq.manufacturer else "غير محدد"
            dept_name = eq.department.name_ar if eq.department else "-"
            w_status = "ساري الضمان" if (eq.warranty_expiry_date and eq.warranty_expiry_date >= today) else "منتهي الضمان"
            if not eq.warranty_expiry_date:
                w_status = "غير محدد"

            rows.append({
                "id": eq.id,
                "manufacturer": manuf_name,
                "asset_number": eq.asset_number or "-",
                "name_ar": eq.name_ar or "-",
                "model": eq.model or "-",
                "serial_number": eq.serial_number or "-",
                "department": dept_name,
                "warranty_status": w_status,
                "status": tr(f"status.{eq.status}", default=eq.status),
                "purchase_price": float(eq.purchase_price or 0.0)
            })

        return {
            "title": "تقرير الأجهزة الطبية حسب الشركة المصنعة",
            "column_keys": column_keys,
            "summary": {
                "total_count": total_count,
                "operational_count": operational_count,
                "under_warranty": under_warranty,
                "total_value": total_value,
                "display": {
                    "إجمالي الأجهزة": total_count,
                    "الأجهزة العاملة": operational_count,
                    "تحت الضمان": under_warranty,
                    "إجمالي القيمة التقديرية": f"{total_value:,.2f} ر.س"
                }
            },
            "headers": [
                "الشركة المصنعة",
                "رقم الأصل",
                "اسم الجهاز",
                "الموديل",
                "الرقم التسلسلي",
                "القسم",
                "حالة الضمان",
                "الحالة التشغيلية",
                "سعر الشراء"
            ],
            "rows": rows
        }

    # ── 6. Vendor & Agent Report ─────────────────────────────────────────────
    def get_vendor_agent_report_data(
        self,
        db: Session,
        vendor_id: Optional[int] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> Dict[str, Any]:
        query = db.query(Equipment)
        if vendor_id and vendor_id != "all":
            query = query.filter(or_(Equipment.agent_id == vendor_id, Equipment.supplier_id == vendor_id))

        items = query.order_by(Equipment.id.desc()).all()

        total_count = len(items)
        operational_count = sum(1 for e in items if e.status == "operational")
        in_maintenance = sum(1 for e in items if e.status == "under_maintenance")

        column_keys = [
            "vendor", "vendor_type", "asset_number", "name_ar", "model",
            "engineer_name", "engineer_phone", "status", "wo_count"
        ]

        rows = []
        for eq in items:
            agent = eq.agent or eq.supplier
            vendor_name = agent.name if agent else "غير محدد"
            v_type = tr(f"vendor.{agent.vendor_type}", default=agent.vendor_type) if agent else "-"
            eng_name = eq.assigned_engineer.name if eq.assigned_engineer else (agent.contact_person if agent else "-")
            eng_phone = eq.assigned_engineer.phone if eq.assigned_engineer else (agent.phone if agent else "-")
            wo_count = len(eq.work_orders) if eq.work_orders else 0

            rows.append({
                "id": eq.id,
                "vendor": vendor_name,
                "vendor_type": v_type,
                "asset_number": eq.asset_number or "-",
                "name_ar": eq.name_ar or "-",
                "model": eq.model or "-",
                "engineer_name": eng_name or "-",
                "engineer_phone": eng_phone or "-",
                "status": tr(f"status.{eq.status}", default=eq.status),
                "wo_count": wo_count
            })

        return {
            "title": "تقرير الأجهزة المرتبطة بالوكلاء والموردين",
            "column_keys": column_keys,
            "summary": {
                "total_count": total_count,
                "operational_count": operational_count,
                "in_maintenance": in_maintenance,
                "display": {
                    "إجمالي الأجهزة المسندة": total_count,
                    "الأجهزة العاملة": operational_count,
                    "تحت الصيانة": in_maintenance
                }
            },
            "headers": [
                "الوكيل / المورد",
                "نوع النشاط",
                "رقم الأصل",
                "اسم الجهاز",
                "الموديل",
                "مهندس الدعم المسؤول",
                "هاتف التواصل",
                "الحالة التشغيلية",
                "أوامر العمل المسجلة"
            ],
            "rows": rows
        }

    # ── 7. Category / Type Report ────────────────────────────────────────────
    def get_category_report_data(
        self,
        db: Session,
        category: Optional[str] = None,
        department_id: Optional[int] = None
    ) -> Dict[str, Any]:
        query = db.query(Equipment)
        if category and category != "all":
            query = query.filter(Equipment.category == category)
        if department_id:
            query = query.filter(Equipment.department_id == department_id)

        items = query.order_by(Equipment.category.asc(), Equipment.id.desc()).all()

        total_count = len(items)
        operational_count = sum(1 for e in items if e.status == "operational")
        high_risk_count = sum(1 for e in items if e.risk_level == "high")

        column_keys = [
            "category", "asset_number", "name_ar", "manufacturer",
            "model", "department", "status", "risk_level"
        ]

        rows = []
        for eq in items:
            dept_name = eq.department.name_ar if eq.department else "-"
            manuf_name = eq.manufacturer.name if eq.manufacturer else "-"

            rows.append({
                "id": eq.id,
                "category": eq.category or "-",
                "asset_number": eq.asset_number or "-",
                "name_ar": eq.name_ar or "-",
                "manufacturer": manuf_name,
                "model": eq.model or "-",
                "department": dept_name,
                "status": tr(f"status.{eq.status}", default=eq.status),
                "risk_level": tr(f"risk.{eq.risk_level}", default=eq.risk_level)
            })

        return {
            "title": "تقرير الأجهزة الطبية حسب نوع الجهاز والتصنيف",
            "column_keys": column_keys,
            "summary": {
                "total_count": total_count,
                "operational_count": operational_count,
                "high_risk_count": high_risk_count,
                "display": {
                    "إجمالي الأجهزة": total_count,
                    "الأجهزة العاملة": operational_count,
                    "أجهزة عالية الخطورة": high_risk_count
                }
            },
            "headers": [
                "نوع الجهاز / التصنيف",
                "رقم الأصل",
                "اسم الجهاز",
                "الشركة المصنعة",
                "الموديل",
                "القسم",
                "الحالة التشغيلية",
                "مستوى الخطورة"
            ],
            "rows": rows
        }

    # ── 8. Department Summary Report ─────────────────────────────────────────
    def get_department_report_data(
        self,
        db: Session,
        department_id: Optional[int] = None
    ) -> Dict[str, Any]:
        dept_query = db.query(Department)
        if department_id:
            dept_query = dept_query.filter(Department.id == department_id)
        departments = dept_query.order_by(Department.name_ar.asc()).all()

        column_keys = [
            "department", "code", "total_equipment", "operational_count",
            "down_count", "open_work_orders", "overdue_pm"
        ]

        today = date.today()
        rows = []
        grand_total = 0
        grand_operational = 0
        grand_down = 0
        grand_open_wo = 0

        for dept in departments:
            eq_list = dept.equipment or []
            total_eq = len(eq_list)
            op_count = sum(1 for e in eq_list if e.status == "operational")
            down_count = sum(1 for e in eq_list if e.status in ("out_of_service", "under_maintenance"))

            eq_ids = [e.id for e in eq_list]
            open_wo = 0
            overdue_pm = 0
            if eq_ids:
                open_wo = db.query(WorkOrder).filter(
                    WorkOrder.equipment_id.in_(eq_ids),
                    WorkOrder.status.in_(("open", "in_progress", "pending", "assigned"))
                ).count()
                overdue_pm = db.query(PMSchedule).filter(
                    PMSchedule.equipment_id.in_(eq_ids),
                    PMSchedule.status == "overdue"
                ).count()

            grand_total += total_eq
            grand_operational += op_count
            grand_down += down_count
            grand_open_wo += open_wo

            rows.append({
                "id": dept.id,
                "department": dept.name_ar,
                "code": dept.code or "-",
                "total_equipment": total_eq,
                "operational_count": op_count,
                "down_count": down_count,
                "open_work_orders": open_wo,
                "overdue_pm": overdue_pm
            })

        return {
            "title": "تقرير الأجهزة والصيانة الشامل حسب القسم الطبي",
            "column_keys": column_keys,
            "summary": {
                "departments_count": len(departments),
                "grand_total": grand_total,
                "grand_operational": grand_operational,
                "grand_down": grand_down,
                "grand_open_wo": grand_open_wo,
                "display": {
                    "عدد الأقسام المشمولة": len(departments),
                    "إجمالي الأجهزة بالمستشفى": grand_total,
                    "إجمالي الأجهزة العاملة": grand_operational,
                    "إجمالي الأجهزة المتوقفة": grand_down,
                    "أوامر العمل المفتوحة": grand_open_wo
                }
            },
            "headers": [
                "القسم الطبي",
                "كود القسم",
                "إجمالي الأجهزة",
                "الأجهزة العاملة",
                "الأجهزة المتوقفة",
                "أوامر العمل المفتوحة",
                "صيانة وقائية متأخرة"
            ],
            "rows": rows
        }

    # ── 9. Warranty Status & Expiry Report ───────────────────────────────────
    def get_warranty_report_data(
        self,
        db: Session,
        warranty_filter: str = "all",
        days_threshold: int = 60,
        department_id: Optional[int] = None
    ) -> Dict[str, Any]:
        today = date.today()
        query = db.query(Equipment)
        if department_id:
            query = query.filter(Equipment.department_id == department_id)

        if warranty_filter == "under_warranty":
            query = query.filter(Equipment.warranty_expiry_date >= today)
        elif warranty_filter == "expired":
            query = query.filter(Equipment.warranty_expiry_date < today)
        elif warranty_filter == "expiring_soon":
            limit_date = today + timedelta(days=days_threshold)
            query = query.filter(Equipment.warranty_expiry_date >= today, Equipment.warranty_expiry_date <= limit_date)

        items = query.order_by(Equipment.warranty_expiry_date.asc()).all()

        total_count = len(items)
        under_warranty_count = sum(1 for e in items if e.warranty_expiry_date and e.warranty_expiry_date >= today)
        expired_count = sum(1 for e in items if e.warranty_expiry_date and e.warranty_expiry_date < today)

        column_keys = [
            "asset_number", "name_ar", "model", "serial_number",
            "department", "vendor", "warranty_expiry", "days_remaining", "warranty_status"
        ]

        rows = []
        for eq in items:
            dept_name = eq.department.name_ar if eq.department else "-"
            agent = eq.agent or eq.supplier
            vendor_name = agent.name if agent else "-"
            w_date_str = eq.warranty_expiry_date.strftime("%Y-%m-%d") if eq.warranty_expiry_date else "غير محدد"

            days_rem = "-"
            status_desc = "غير مسجل"
            if eq.warranty_expiry_date:
                delta = (eq.warranty_expiry_date - today).days
                days_rem = str(delta)
                if delta > 30:
                    status_desc = "ساري الضمان"
                elif delta >= 0:
                    status_desc = "يوشك على الانتهاء"
                else:
                    status_desc = f"منتهي ({abs(delta)} يوم)"

            rows.append({
                "id": eq.id,
                "asset_number": eq.asset_number or "-",
                "name_ar": eq.name_ar or "-",
                "model": eq.model or "-",
                "serial_number": eq.serial_number or "-",
                "department": dept_name,
                "vendor": vendor_name,
                "warranty_expiry": w_date_str,
                "days_remaining": days_rem,
                "warranty_status": status_desc
            })

        return {
            "title": "تقرير متابعة عقود الضمان وانتهاء الصلاحية",
            "column_keys": column_keys,
            "summary": {
                "total_count": total_count,
                "under_warranty_count": under_warranty_count,
                "expired_count": expired_count,
                "display": {
                    "إجمالي الأجهزة": total_count,
                    "تحت الضمان الساري": under_warranty_count,
                    "أجهزة منتهية الضمان": expired_count
                }
            },
            "headers": [
                "رقم الأصل",
                "اسم الجهاز",
                "الموديل",
                "الرقم التسلسلي",
                "القسم",
                "الوكيل / المورد",
                "تاريخ نهاية الضمان",
                "الأيام المتبقية",
                "حالة الضمان"
            ],
            "rows": rows
        }

    # ── 10. Periodic Maintenance Summary Report ──────────────────────────────
    def get_periodic_maintenance_report_data(
        self,
        db: Session,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        department_id: Optional[int] = None
    ) -> Dict[str, Any]:
        query = db.query(WorkOrder)
        if from_date:
            query = query.filter(WorkOrder.created_at >= datetime.combine(from_date, datetime.min.time()))
        if to_date:
            query = query.filter(WorkOrder.created_at <= datetime.combine(to_date, datetime.max.time()))
        if department_id:
            query = query.join(Equipment).filter(Equipment.department_id == department_id)

        orders = query.order_by(WorkOrder.created_at.desc()).all()

        total_orders = len(orders)
        completed_orders = sum(1 for o in orders if o.status in ("completed", "closed"))
        total_cost = sum(float(o.total_cost or 0.0) for o in orders)

        column_keys = [
            "work_order_number", "reported_date", "equipment", "department",
            "priority", "status", "technician", "failure_description", "total_cost"
        ]

        rows = []
        for o in orders:
            eq_name = f"{o.equipment.name_ar} ({o.equipment.asset_number})" if o.equipment else "-"
            dept_name = o.equipment.department.name_ar if (o.equipment and o.equipment.department) else "-"
            tech_name = o.assigned_technician.full_name if o.assigned_technician else "-"

            rows.append({
                "id": o.id,
                "work_order_number": o.work_order_number,
                "reported_date": o.created_at.strftime("%Y-%m-%d") if o.created_at else "-",
                "equipment": eq_name,
                "department": dept_name,
                "priority": tr(f"priority.{o.priority}", default=o.priority),
                "status": tr(f"status.{o.status}", default=o.status),
                "technician": tech_name,
                "failure_description": o.failure_description or "-",
                "total_cost": float(o.total_cost or 0.0)
            })

        return {
            "title": "تقرير ملخص أعمال الصيانة الدورية والتكاليف",
            "column_keys": column_keys,
            "summary": {
                "total_orders": total_orders,
                "completed_orders": completed_orders,
                "total_cost": total_cost,
                "display": {
                    "إجمالي البلاغات المسجلة": total_orders,
                    "البلاغات المكتملة": completed_orders,
                    "التكلفة الإجمالية للصيانة": f"{total_cost:,.2f} ر.س"
                }
            },
            "headers": [
                "رقم أمر العمل",
                "تاريخ البلاغ",
                "الجهاز الطبي",
                "القسم",
                "الأولوية",
                "الحالة",
                "الفني المسؤول",
                "وصف العطل",
                "التكلفة (ر.س)"
            ],
            "rows": rows
        }

    # ── 5. Excel Export Function ─────────────────────────────────────────────
    def export_to_excel(self, report_data: Dict[str, Any], filepath: str):
        """Export a consistently styled Arabic RTL worksheet with bounded widths and print settings."""
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.utils import get_column_letter

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "تقرير MEMMS"
        ws.sheet_view.rightToLeft = True

        title = report_data.get("title", "تقرير الصيانة والأجهزة الطبية")
        summary = report_data.get("summary", {})
        display_summary = summary.get("display", {k: v for k, v in summary.items() if k != "display"})
        headers = report_data.get("headers", [])
        column_keys = report_data.get("column_keys", [])
        rows = report_data.get("rows", [])
        column_count = max(len(headers), 1)
        last_col = get_column_letter(column_count)

        teal = "0F766E"
        dark = "172033"
        border_color = "CBD5E1"
        thin = Side(style="thin", color=border_color)
        cell_border = Border(left=thin, right=thin, top=thin, bottom=thin)

        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=column_count)
        title_cell = ws.cell(row=1, column=1, value=f"هيئة مستشفى الثورة العام النموذجي — صنعاء | {title}")
        title_cell.font = Font(name="Arial", size=15, bold=True, color="FFFFFF")
        title_cell.fill = PatternFill("solid", fgColor=teal)
        title_cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True, readingOrder=2)
        ws.row_dimensions[1].height = 34

        ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=column_count)
        date_cell = ws.cell(row=2, column=1, value=f"تاريخ استخراج التقرير: {datetime.now().strftime('%Y-%m-%d %H:%M')} | نظام MEMMS")
        date_cell.font = Font(name="Arial", size=10, color="64748B")
        date_cell.alignment = Alignment(horizontal="center", vertical="center", readingOrder=2)
        ws.row_dimensions[2].height = 22

        row_idx = 4
        if display_summary:
            ws.merge_cells(start_row=row_idx, start_column=1, end_row=row_idx, end_column=column_count)
            label_cell = ws.cell(row=row_idx, column=1, value="ملخص المؤشرات والإحصائيات")
            label_cell.font = Font(name="Arial", size=11, bold=True, color=teal)
            label_cell.alignment = Alignment(horizontal="right", vertical="center", readingOrder=2)
            row_idx += 1
            for key, value in display_summary.items():
                c1 = ws.cell(row=row_idx, column=1, value=str(key))
                c1.font = Font(name="Arial", size=10, bold=True, color="475569")
                c1.alignment = Alignment(horizontal="right", vertical="center", wrap_text=True, readingOrder=2)
                c2 = ws.cell(row=row_idx, column=2, value=value if isinstance(value, (int, float)) else str(value))
                c2.font = Font(name="Arial", size=10, bold=True, color=teal)
                c2.alignment = Alignment(horizontal="right", vertical="center", wrap_text=True, readingOrder=2)
                for cell in (c1, c2):
                    cell.border = cell_border
                row_idx += 1
            row_idx += 1

        header_row = row_idx
        for col_idx, header in enumerate(headers, 1):
            cell = ws.cell(row=header_row, column=col_idx, value=header)
            cell.fill = PatternFill("solid", fgColor=teal)
            cell.font = Font(name="Arial", size=10, bold=True, color="FFFFFF")
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True, readingOrder=2)
            cell.border = cell_border
        ws.row_dimensions[header_row].height = 32

        for offset, record in enumerate(rows, 1):
            row_idx = header_row + offset
            for col_idx, key in enumerate(column_keys, 1):
                value = record.get(key, "")
                cell = ws.cell(row=row_idx, column=col_idx, value=value)
                cell.font = Font(name="Arial", size=10, color=dark)
                cell.alignment = Alignment(
                    horizontal="center" if isinstance(value, (int, float)) else "right",
                    vertical="top", wrap_text=True, readingOrder=2
                )
                cell.border = cell_border
                if offset % 2 == 0:
                    cell.fill = PatternFill("solid", fgColor="F8FAFC")
            ws.row_dimensions[row_idx].height = 30

        # Cap widths so long descriptions do not make the worksheet excessively wide.
        for col_idx in range(1, column_count + 1):
            letter = get_column_letter(col_idx)
            header_text = str(headers[col_idx - 1]) if col_idx <= len(headers) else ""
            key = column_keys[col_idx - 1] if col_idx <= len(column_keys) else ""
            max_len = len(header_text)
            for record in rows:
                max_len = max(max_len, min(len(str(record.get(key, "") or "")), 42))
            ws.column_dimensions[letter].width = min(max(max_len + 3, 14), 34)

        ws.freeze_panes = f"A{header_row + 1}"
        ws.auto_filter.ref = f"A{header_row}:{last_col}{header_row + len(rows)}" if rows else f"A{header_row}:{last_col}{header_row}"
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        ws.page_setup.fitToWidth = 1
        ws.page_setup.fitToHeight = 0
        ws.page_setup.orientation = "landscape" if len(headers) > 7 else "portrait"
        ws.page_setup.paperSize = ws.PAPERSIZE_A4
        ws.page_margins.left = 0.25
        ws.page_margins.right = 0.25
        ws.page_margins.top = 0.5
        ws.page_margins.bottom = 0.5
        ws.print_title_rows = f"{header_row}:{header_row}"
        ws.print_area = f"A1:{last_col}{header_row + len(rows)}"
        wb.save(filepath)

    # ── 6. CSV Export Function ───────────────────────────────────────────────
    def export_to_csv(self, report_data: Dict[str, Any], filepath: str):
        headers = report_data.get("headers", [])
        column_keys = report_data.get("column_keys", [])
        rows = report_data.get("rows", [])

        with open(filepath, mode="w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([f"MEMMS — {report_data.get('title', 'التقرير')}"])
            writer.writerow([f"تاريخ التقرير: {datetime.now().strftime('%Y-%m-%d %H:%M')}"])
            writer.writerow([])
            writer.writerow(headers)

            for row in rows:
                row_values = [row.get(k, "") for k in column_keys]
                writer.writerow(row_values)

    def prepare_rtl_document(self, doc, html: str, font_size: int = 9, default_font: str = "Segoe UI"):
        """
        Sets up QTextDocument to strictly format RTL Arabic layouts,
        enforcing Right-to-Left on both paragraph options and all internal QTextTables.
        """
        from PySide6.QtGui import QFont, QTextOption, QTextTable, QTextFrameFormat, QTextLength, QBrush, QColor
        from PySide6.QtCore import Qt

        doc.setDefaultFont(QFont(default_font, font_size))
        opt = doc.defaultTextOption()
        opt.setTextDirection(Qt.LayoutDirection.RightToLeft)
        opt.setAlignment(Qt.AlignmentFlag.AlignRight)
        doc.setDefaultTextOption(opt)

        doc.setHtml(html)

        root = doc.rootFrame()
        if root:
            for child in root.childFrames():
                if isinstance(child, QTextTable):
                    fmt = child.format()
                    fmt.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
                    fmt.setAlignment(Qt.AlignmentFlag.AlignRight)
                    fmt.setWidth(QTextLength(QTextLength.Type.PercentageLength, 100.0))
                    if fmt.border() > 0:
                        fmt.setBorder(1.0)
                        fmt.setBorderBrush(QBrush(QColor("#CBD5E1")))
                        fmt.setBorderStyle(QTextFrameFormat.BorderStyle.BorderStyle_Solid)
                        fmt.setCellPadding(5.0)
                        fmt.setCellSpacing(0.0)
                    child.setFormat(fmt)

    # ── 7. HTML / Printable Document Export ──────────────────────────────────
    @staticmethod
    def get_page_orientation(report_data: Dict[str, Any]) -> str:
        """Choose A4 orientation from the report's actual layout."""
        if report_data.get("is_single_equipment"):
            return "landscape"
        if report_data.get("is_work_order_ticket"):
            return "portrait"
        return "landscape" if len(report_data.get("headers", [])) > 7 else "portrait"

    @staticmethod
    def _bidi_text(value: Any) -> str:
        """
        Format values for robust BiDi (Bidirectional) Arabic RTL display.
        Protects pure LTR codes/numbers/dates and mixed parentheticals
        from being scrambled or inverted by BiDi algorithms in Qt/WebKit.
        """
        if value is None or value == "":
            return "—"
        if isinstance(value, float):
            value = f"{value:,.2f}"
        s = str(value).strip()
        if not s:
            return "—"

        escaped = html_escape(s, quote=True)
        # Check if text contains Arabic characters
        has_arabic = bool(re.search(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]', s))
        if not has_arabic:
            # Pure LTR string (codes, serials, dates, floats, English names):
            # Wrap with Left-to-Right Marks (&lrm;)
            return f"&lrm;{escaped}&lrm;"

        # Mixed string (Arabic + English / Codes / Numbers / Parentheses):
        def wrap_lrm(m):
            return f"&lrm;{m.group(0)}&lrm;"

        # 1. Protect parenthesized Latin/numbers/symbols like (Asset Tag), (S/N), (HS 5090), (Life-Supporting)
        res = re.sub(r'\([A-Za-z0-9\s\-_/.:+]+\)', wrap_lrm, escaped)
        # 2. Protect isolated LTR words/codes that contain hyphens or numbers (like WO-THW-2026-001)
        res = re.sub(r'(?<![A-Za-z0-9&])([A-Za-z0-9]+[-_][A-Za-z0-9\-_]+)(?![A-Za-z0-9;])', wrap_lrm, res)
        return res

    @staticmethod
    def _html_value(value: Any) -> str:
        """Format and escape user/database text before placing it in an HTML report."""
        return ReportService._bidi_text(value)

    @staticmethod
    def _html_table(headers: List[str], rows: List[List[Any]], empty_text: str = "لا توجد بيانات متاحة لهذا القسم") -> str:
        """
        Render all report tables using consistent RTL table design.
        In Qt QTextDocument, columns are physically ordered left-to-right (increasing X),
        so to achieve true Arabic right-to-left layout where the first column appears on the right,
        the column order is reversed for HTML serialization.
        """
        if not headers:
            headers = []

        rev_headers = list(reversed(headers))
        head = "".join(f'<th bgcolor="#0F766E" align="center"><font color="#FFFFFF">{ReportService._html_value(item)}</font></th>' for item in rev_headers)

        if rows:
            body_rows = []
            for r_idx, row in enumerate(rows):
                rev_row = list(reversed(row))
                bg = ' bgcolor="#F8FAFC"' if r_idx % 2 == 1 else ''
                cells = "".join(f'<td{bg} align="right">{ReportService._html_value(value)}</td>' for value in rev_row)
                body_rows.append(f"<tr>{cells}</tr>")
            body = "".join(body_rows)
        else:
            body = f'<tr><td class="empty" colspan="{max(len(headers), 1)}">{ReportService._html_value(empty_text)}</td></tr>'

        return (
            '<table dir="rtl" class="data-table" width="100%" border="1" cellpadding="5" cellspacing="0">'
            '<thead><tr>' + head + '</tr></thead>'
            '<tbody>' + body + '</tbody></table>'
        )

    @staticmethod
    def _html_info_table(pairs: List[tuple]) -> str:
        """
        Render label/value pairs in a consistent two-pair-per-row RTL grid.
        For Qt QTextDocument RTL, physical columns are left-to-right:
        Col 0: Value 2 (left)
        Col 1: Label 2 (mid-left)
        Col 2: Value 1 (mid-right)
        Col 3: Label 1 (right)
        So an Arabic reader reading Right-to-Left sees: Label 1 -> Value 1 -> Label 2 -> Value 2.
        """
        rows = []
        for index in range(0, len(pairs), 2):
            row_pairs = pairs[index:index + 2]
            if len(row_pairs) == 2:
                l1, v1 = row_pairs[0]
                l2, v2 = row_pairs[1]
                rows.append(
                    '<tr>'
                    f'<td class="info-value" width="32%" align="right">{ReportService._html_value(v2)}</td>'
                    f'<th class="info-label" width="18%" align="right">{ReportService._html_value(l2)}</th>'
                    f'<td class="info-value" width="32%" align="right">{ReportService._html_value(v1)}</td>'
                    f'<th class="info-label" width="18%" align="right">{ReportService._html_value(l1)}</th>'
                    '</tr>'
                )
            else:
                l1, v1 = row_pairs[0]
                rows.append(
                    '<tr>'
                    f'<td class="info-value" colspan="3" width="82%" align="right">{ReportService._html_value(v1)}</td>'
                    f'<th class="info-label" width="18%" align="right">{ReportService._html_value(l1)}</th>'
                    '</tr>'
                )
        return '<table dir="rtl" class="info-table" width="100%" border="1" cellpadding="6" cellspacing="0"><tbody>' + "".join(rows) + '</tbody></table>'

    @staticmethod
    def _html_summary(summary: Dict[str, Any]) -> str:
        display = summary.get("display", {key: value for key, value in summary.items() if key != "display"})
        if not display:
            return ""
        cells = []
        for label, value in display.items():
            cells.append(
                f'<td class="summary-card" align="center"><div class="summary-label">{ReportService._html_value(label)}</div>'
                f'<div class="summary-value">{ReportService._html_value(value)}</div></td>'
            )
        # Reverse cells so the first summary card appears on the right in RTL
        cells.reverse()
        return '<table dir="rtl" class="summary-table" width="100%" border="0" cellpadding="4" cellspacing="4"><tbody><tr>' + "".join(cells) + '</tr></tbody></table>'

    def _html_document(self, title: str, content: str, report_data: Optional[Dict[str, Any]] = None) -> str:
        """Shared Arabic-first A4 report shell used by every printable report."""
        orientation = self.get_page_orientation(report_data or {})
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        safe_title = self._html_value(title)
        page_mode = "landscape" if orientation == "landscape" else "portrait"
        return f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="utf-8">
<title>{safe_title}</title>
<style>
@page {{ size: A4 {page_mode}; margin: 12mm; }}
* {{ box-sizing: border-box; }}
html, body {{ direction: rtl; unicode-bidi: embed; }}
body {{ font-family: "Segoe UI", Tahoma, Arial, sans-serif; color: #172033; font-size: 10pt; line-height: 1.45; margin: 0; padding: 0; text-align: right; }}
.header {{ direction: rtl; text-align: center; border-bottom: 2pt solid #0F766E; padding: 0 0 9pt; margin: 0 0 12pt; }}
.brand {{ font-size: 15pt; font-weight: bold; color: #0F766E; margin: 0 0 4pt; }}
.title {{ font-size: 14pt; font-weight: bold; color: #172033; margin: 2pt 0 5pt; }}
.meta {{ font-size: 9pt; color: #64748B; }}
h2.section {{ direction: rtl; text-align: right; background: #E8F4F2; color: #115E59; border-right: 3pt solid #0F766E; padding: 5pt 8pt; margin: 12pt 0 5pt; font-size: 11pt; page-break-after: avoid; }}
.summary-table, .info-table, .data-table {{ direction: rtl; width: 100%; border-collapse: collapse; margin: 6pt 0 10pt; }}
.summary-table {{ border-collapse: separate; border-spacing: 4pt; table-layout: auto; }}
.summary-card {{ border: 1pt solid #CBD5E1; background: #F8FAFC; padding: 6pt; text-align: center; vertical-align: middle; }}
.summary-label {{ color: #475569; font-size: 9pt; font-weight: bold; }}
.summary-value {{ color: #0F766E; font-size: 12pt; font-weight: bold; margin-top: 2pt; }}
.info-table {{ table-layout: fixed; }}
.info-label {{ width: 18%; background: #F1F5F9; color: #334155; font-weight: bold; text-align: right; font-size: 9pt; }}
.info-value {{ width: 32%; text-align: right; overflow-wrap: anywhere; font-size: 9pt; }}
.info-table th, .info-table td {{ border: 1pt solid #CBD5E1; padding: 6pt; vertical-align: top; }}
.data-table {{ table-layout: auto; }}
.data-table th {{ background: #0F766E; color: #FFFFFF; font-weight: bold; text-align: center; font-size: 9pt; padding: 6pt 5pt; border: 1pt solid #0B625C; }}
.data-table td {{ text-align: right; vertical-align: top; font-size: 9pt; padding: 5pt; border: 1pt solid #CBD5E1; overflow-wrap: anywhere; word-wrap: break-word; }}
.data-table tbody tr:nth-child(even) {{ background: #F8FAFC; }}
.data-table thead {{ display: table-header-group; }}
.data-table tr {{ page-break-inside: avoid; }}
.empty {{ text-align: center !important; color: #64748B; padding: 12pt !important; }}
.note-box {{ border: 1pt solid #CBD5E1; background: #F8FAFC; padding: 8pt; margin: 5pt 0 9pt; white-space: pre-wrap; overflow-wrap: anywhere; }}
.costs {{ width: 58%; margin-right: 0; margin-left: auto; }}
.signatures {{ width: 100%; margin-top: 22pt; border-collapse: collapse; direction: rtl; }}
.signatures td {{ width: 33.3%; padding: 12pt 8pt 4pt; border-top: 1pt solid #94A3B8; text-align: center; vertical-align: top; }}
.footer {{ margin-top: 14pt; padding-top: 5pt; border-top: 1pt solid #CBD5E1; color: #64748B; font-size: 8pt; text-align: center; direction: rtl; }}
</style>
</head>
<body dir="rtl">
<div class="header">
<div class="brand">هيئة مستشفى الثورة العام النموذجي — صنعاء</div>
<div class="title">{safe_title}</div>
<div class="meta">الإدارة العامة للشؤون الهندسية والصيانة الطبية | تاريخ استخراج التقرير: &lrm;{now_str}&lrm; | نظام MEMMS</div>
</div>
{content}
<div class="footer">وثيقة صادرة آليًا من نظام إدارة صيانة الأجهزة الطبية (MEMMS) — هيئة مستشفى الثورة العام النموذجي بصنعاء</div>
</body>
</html>"""

    def generate_html_report(self, report_data: Dict[str, Any]) -> str:
        """Build the standard Arabic RTL HTML template for A4 PDF and print output."""
        if report_data.get("is_single_equipment"):
            return self.generate_equipment_history_html(report_data)
        if report_data.get("is_work_order_ticket"):
            return self.generate_work_order_ticket_html(report_data)

        title = report_data.get("title", "تقرير الصيانة والأجهزة الطبية")
        summary_html = self._html_summary(report_data.get("summary", {}))
        headers = report_data.get("headers", [])
        keys = report_data.get("column_keys", [])
        rows = report_data.get("rows", [])
        table_rows = [[row.get(key, "—") for key in keys] for row in rows]
        content = summary_html + self._html_table(headers, table_rows)
        return self._html_document(title, content, report_data)

    def generate_receiving_report_html(self, report_data: Dict[str, Any]) -> str:
        """Generate the receiving/commissioning record with the shared Arabic RTL report design."""
        eq = report_data.get("equipment", {})
        rec = report_data.get("receiving", {})
        content = '<h2 class="section">أولًا: بيانات الجهاز الطبي</h2>'
        content += self._html_info_table([
            ("اسم الجهاز", eq.get("name_ar")), ("رقم الأصل", eq.get("asset_number")),
            ("الموديل", eq.get("model")), ("الرقم التسلسلي", eq.get("serial_number")),
            ("القسم الطبي", eq.get("department")), ("الشركة المصنعة", eq.get("manufacturer"))
        ])
        content += '<h2 class="section">ثانيًا: بيانات الاستلام والتعميد</h2>'
        content += self._html_info_table([
            ("رقم التعميد", rec.get("commissioning_number")), ("تاريخ التعميد", rec.get("commissioning_date")),
            ("تاريخ استلام الجهاز", rec.get("receipt_date")), ("رقم محضر الاستلام", rec.get("receipt_report_number")),
            ("فني الاستلام", rec.get("receiving_technician_name")), ("مسؤول التسجيل", rec.get("registration_officer_name")),
            ("تاريخ التسجيل", rec.get("registration_date")), ("ملاحظات الاستلام", rec.get("receipt_notes"))
        ])
        content += """<table dir="rtl" class="signatures" width="100%" border="0" cellpadding="4" cellspacing="0" style="margin-top: 22pt; border-collapse: collapse;"><tbody><tr>
<td width="33.3%" align="center" style="vertical-align: top; padding: 12pt 8pt 4pt; border: none; border-top: 1pt solid #94A3B8;"><strong>رئيس القسم الهندسي</strong><br><br>الاعتماد والختم: ........................</td>
<td width="33.3%" align="center" style="vertical-align: top; padding: 12pt 8pt 4pt; border: none; border-top: 1pt solid #94A3B8;"><strong>مسؤول تسجيل الجهاز</strong><br><br>الاسم والتوقيع: ........................</td>
<td width="33.3%" align="center" style="vertical-align: top; padding: 12pt 8pt 4pt; border: none; border-top: 1pt solid #94A3B8;"><strong>فني الاستلام</strong><br><br>الاسم والتوقيع: ........................</td>
</tr></tbody></table>"""
        return self._html_document("محضر استلام وتعميد جهاز طبي", content, report_data)

    # ── 8. Single Equipment Maintenance History Report ───────────────────────
    def get_equipment_history_report_data(self, db: Session, equipment_id: int) -> Dict[str, Any]:
        """Gathers full lifecycle maintenance history for a single medical asset."""
        eq = db.query(Equipment).filter_by(id=equipment_id).first()
        if not eq:
            return {}

        work_orders = db.query(WorkOrder).filter_by(equipment_id=eq.id).order_by(WorkOrder.created_at.desc()).all()
        pm_schedules = db.query(PMSchedule).filter_by(equipment_id=eq.id).order_by(PMSchedule.due_date.desc()).all()

        wo_ids = [w.id for w in work_orders]
        parts_consumed = []
        if wo_ids:
            parts_consumed = db.query(WorkOrderPart).filter(WorkOrderPart.work_order_id.in_(wo_ids)).all()

        total_wo = len(work_orders)
        completed_wo = sum(1 for w in work_orders if w.status in ("completed", "closed"))
        open_wo = sum(1 for w in work_orders if w.status in ("open", "pending", "assigned", "in_progress", "waiting_parts"))
        total_maint_cost = sum(float(w.total_cost or 0.0) for w in work_orders)
        total_parts_cost = sum(float(w.total_parts_cost or 0.0) for w in work_orders)
        total_labor_cost = sum(float(w.total_labor_cost or 0.0) for w in work_orders)

        cost_ratio = (total_maint_cost / float(eq.purchase_price) * 100) if (eq.purchase_price and eq.purchase_price > 0) else 0.0

        wo_rows = []
        for w in work_orders:
            wo_rows.append({
                "work_order_number": w.work_order_number,
                "created_at": w.created_at.strftime("%Y-%m-%d") if w.created_at else "-",
                "priority": tr(f"priority.{w.priority}", default=w.priority),
                "status": tr(f"status.{w.status}", default=w.status),
                "technician": w.assigned_technician.full_name if w.assigned_technician else "غير مخصص",
                "failure_description": w.failure_description or "-",
                "resolution_notes": w.corrective_action or w.diagnosis or "-",
                "total_cost": float(w.total_cost or 0.0)
            })

        pm_rows = []
        for pm in pm_schedules:
            tech_name = pm.execution.technician.full_name if (pm.execution and pm.execution.technician) else "غير مخصص"
            plan_title = pm.plan.title if (pm.plan and hasattr(pm.plan, "title")) else (getattr(pm.plan, "name_ar", "-") if pm.plan else "-")
            pm_rows.append({
                "schedule_code": f"PM-{pm.id:04d}",
                "plan_name": plan_title,
                "scheduled_date": pm.due_date.strftime("%Y-%m-%d") if pm.due_date else "-",
                "status": tr(f"status.{pm.status}", default=pm.status),
                "technician": tech_name,
            })

        part_rows = []
        for wp in parts_consumed:
            p_name = wp.part.name_ar if (wp.part and wp.part.name_ar) else (wp.part.name_en if wp.part else "-")
            part_rows.append({
                "part_number": wp.part.part_number if wp.part else "-",
                "name": p_name,
                "quantity": float(wp.quantity or 0.0),
                "unit_price": float(wp.unit_price or 0.0),
                "total_price": float(wp.total_price or 0.0),
            })

        dept_name = eq.department.name_ar if eq.department else "-"
        loc_name = eq.location.room_name if eq.location else "-"
        manuf_name = eq.manufacturer.name if eq.manufacturer else "-"
        agent_name = eq.agent.name if eq.agent else "-"

        criticality_text = tr(f"criticality.{eq.criticality}", default=eq.criticality)
        risk_text = tr(f"risk.{eq.risk_level}", default=eq.risk_level)
        status_text = tr(f"status.{eq.status}", default=eq.status)

        column_keys = ["work_order_number", "created_at", "priority", "status", "technician", "failure_description", "total_cost"]
        headers = ["رقم أمر العمل", "التاريخ", "الأولوية", "الحالة", "الفني المكلف", "وصف العطل", "التكلفة (ر.س)"]

        return {
            "title": f"بطاقة السجل الفني وتاريخ صيانة الجهاز: {eq.name_ar or eq.name_en} ({eq.asset_number})",
            "is_single_equipment": True,
            "equipment": {
                "id": eq.id,
                "asset_number": eq.asset_number,
                "serial_number": eq.serial_number,
                "name_ar": eq.name_ar or "-",
                "name_en": eq.name_en or "-",
                "model": eq.model or "-",
                "category": eq.category or "-",
                "department": dept_name,
                "location": loc_name,
                "manufacturer": manuf_name,
                "agent": agent_name,
                "status": status_text,
                "risk_level": risk_text,
                "criticality": criticality_text,
                "purchase_date": eq.purchase_date.strftime("%Y-%m-%d") if eq.purchase_date else "-",
                "installation_date": eq.installation_date.strftime("%Y-%m-%d") if eq.installation_date else "-",
                "warranty_expiry": eq.warranty_expiry_date.strftime("%Y-%m-%d") if eq.warranty_expiry_date else "-",
                "purchase_price": float(eq.purchase_price or 0.0),
                "notes": eq.notes or "-",
            },
            "summary": {
                "total_orders": total_wo,
                "completed_orders": completed_wo,
                "open_orders": open_wo,
                "total_maint_cost": total_maint_cost,
                "total_parts_cost": total_parts_cost,
                "total_labor_cost": total_labor_cost,
                "cost_ratio": cost_ratio,
                "display": {
                    "إجمالي أوامر الصيانة": total_wo,
                    "البلاغات المكتملة": completed_wo,
                    "البلاغات المفتوحة": open_wo,
                    "إجمالي تكاليف الصيانة": f"{total_maint_cost:,.2f} ر.س",
                    "نسبة الصيانة لسعر الشراء": f"{cost_ratio:.1f}%"
                }
            },
            "headers": headers,
            "column_keys": column_keys,
            "rows": wo_rows,
            "work_orders": wo_rows,
            "pm_schedules": pm_rows,
            "parts_consumed": part_rows
        }

    def generate_equipment_history_html(self, report_data: Dict[str, Any]) -> str:
        """Generate the equipment passport and maintenance history using the shared RTL template."""
        eq = report_data.get("equipment", {})
        summary = report_data.get("summary", {})
        content = self._html_summary(summary)
        content += '<h2 class="section">أولًا: البيانات التعريفية للجهاز</h2>'
        equipment_pairs = [
            ("رقم الأصل", eq.get("asset_number")), ("اسم الجهاز", eq.get("name_ar")),
            ("الاسم بالإنجليزية", eq.get("name_en")), ("الرقم التسلسلي", eq.get("serial_number")),
            ("الشركة المصنعة", eq.get("manufacturer")), ("الموديل", eq.get("model")),
            ("القسم الطبي", eq.get("department")), ("الموقع", eq.get("location")),
            ("التصنيف", eq.get("category")), ("الحالة التشغيلية", eq.get("status")),
            ("درجة الخطورة", eq.get("risk_level")), ("الأهمية", eq.get("criticality")),
            ("تاريخ الشراء", eq.get("purchase_date")), ("تاريخ التركيب", eq.get("installation_date")),
            ("انتهاء الضمان", eq.get("warranty_expiry")),
            ("سعر الشراء (ر.س)", eq.get("purchase_price")), ("الوكيل", eq.get("agent")),
            ("ملاحظات", eq.get("notes"))
        ]
        content += self._html_info_table(equipment_pairs)

        wo_rows = [[w.get("work_order_number"), w.get("created_at"), w.get("priority"),
                    w.get("status"), w.get("technician"), w.get("failure_description"),
                    w.get("total_cost", 0)] for w in report_data.get("work_orders", [])]
        content += '<h2 class="section">ثانيًا: سجل أوامر الصيانة والأعطال</h2>'
        content += self._html_table(
            ["رقم الأمر", "تاريخ البلاغ", "الأولوية", "الحالة", "الفني المسؤول", "وصف العطل", "التكلفة (ر.س)"],
            wo_rows, "لا توجد أوامر صيانة مسجلة لهذا الجهاز"
        )

        pm_rows = [[p.get("schedule_code"), p.get("plan_name"), p.get("scheduled_date"),
                    p.get("status"), p.get("technician")] for p in report_data.get("pm_schedules", [])]
        content += '<h2 class="section">ثالثًا: سجل الصيانة الوقائية</h2>'
        content += self._html_table(
            ["رقم الجدول", "خطة الصيانة", "التاريخ المجدول", "الحالة", "الفني المسؤول"],
            pm_rows, "لا توجد جداول صيانة وقائية مرتبطة بهذا الجهاز"
        )

        part_rows = [[p.get("part_number"), p.get("name"), p.get("quantity"),
                      p.get("unit_price", 0), p.get("total_price", 0)]
                     for p in report_data.get("parts_consumed", [])]
        content += '<h2 class="section">رابعًا: قطع الغيار المستهلكة</h2>'
        content += self._html_table(
            ["رقم القطعة", "اسم القطعة", "الكمية", "سعر الوحدة (ر.س)", "الإجمالي (ر.س)"],
            part_rows, "لم يتم تسجيل صرف قطع غيار لهذا الجهاز"
        )
        content += """<table dir="rtl" class="signatures" width="100%" border="0" cellpadding="4" cellspacing="0" style="margin-top: 22pt; border-collapse: collapse;"><tbody><tr>
<td width="33.3%" align="center" style="vertical-align: top; padding: 12pt 8pt 4pt; border: none; border-top: 1pt solid #94A3B8;"><strong>اعتماد الإدارة</strong><br><br>التوقيع والختم: ........................</td>
<td width="33.3%" align="center" style="vertical-align: top; padding: 12pt 8pt 4pt; border: none; border-top: 1pt solid #94A3B8;"><strong>رئيس قسم الهندسة الطبية</strong><br><br>الاسم والتوقيع: ........................</td>
<td width="33.3%" align="center" style="vertical-align: top; padding: 12pt 8pt 4pt; border: none; border-top: 1pt solid #94A3B8;"><strong>الفني / المهندس المسؤول</strong><br><br>الاسم والتوقيع: ........................</td>
</tr></tbody></table>"""
        return self._html_document(
            "بطاقة السجل الفني وتاريخ صيانة الجهاز الطبي", content, report_data
        )

    # ── 9. Individual Work Order Maintenance Ticket / Job Sheet ──────────────
    def get_work_order_ticket_data(self, db: Session, work_order_id: int) -> Dict[str, Any]:
        """Gathers single work order ticket details with parts and equipment profile."""
        wo = db.query(WorkOrder).filter_by(id=work_order_id).first()
        if not wo:
            return {}

        eq = wo.equipment
        parts = db.query(WorkOrderPart).filter_by(work_order_id=wo.id).all()

        part_rows = []
        for p in parts:
            p_name = p.part.name_ar if (p.part and p.part.name_ar) else (p.part.name_en if p.part else "-")
            part_rows.append({
                "part_number": p.part.part_number if p.part else "-",
                "name": p_name,
                "quantity": float(p.quantity or 0.0),
                "unit_price": float(p.unit_price or 0.0),
                "total_price": float(p.total_price or 0.0)
            })

        return {
            "title": f"إشعار وتذكرة أمر صيانة رقم {wo.work_order_number}",
            "is_work_order_ticket": True,
            "work_order": {
                "id": wo.id,
                "number": wo.work_order_number,
                "created_at": wo.created_at.strftime("%Y-%m-%d %H:%M") if wo.created_at else "-",
                "completed_at": wo.completed_at.strftime("%Y-%m-%d %H:%M") if wo.completed_at else "-",
                "priority": tr(f"priority.{wo.priority}", default=wo.priority),
                "status": tr(f"status.{wo.status}", default=wo.status),
                "reported_by": wo.reported_by_name or "-",
                "department": wo.department.name_ar if wo.department else (eq.department.name_ar if eq and eq.department else "-"),
                "technician": wo.assigned_technician.full_name if wo.assigned_technician else "غير مخصص",
                "failure_description": wo.failure_description or "-",
                "resolution_notes": wo.corrective_action or wo.diagnosis or "-",
                "labor_cost": float(wo.total_labor_cost or 0.0),
                "parts_cost": float(wo.total_parts_cost or 0.0),
                "total_cost": float(wo.total_cost or 0.0)
            },
            "equipment": {
                "asset_number": eq.asset_number if eq else "-",
                "serial_number": eq.serial_number if eq else "-",
                "name_ar": eq.name_ar if eq else "-",
                "model": eq.model if eq else "-",
                "criticality": tr(f"criticality.{eq.criticality}", default=eq.criticality) if eq else "-",
                "risk_level": tr(f"risk.{eq.risk_level}", default=eq.risk_level) if eq else "-"
            } if eq else {},
            "parts": part_rows
        }

    def generate_work_order_ticket_html(self, report_data: Dict[str, Any]) -> str:
        """Generate the work order ticket with the same Arabic RTL identity and A4 layout."""
        wo = report_data.get("work_order", {})
        eq = report_data.get("equipment", {})
        content = '<h2 class="section">أولًا: بيانات أمر الصيانة والبلاغ</h2>'
        content += self._html_info_table([
            ("رقم أمر الصيانة", wo.get("number")), ("تاريخ ووقت البلاغ", wo.get("created_at")),
            ("الأولوية", wo.get("priority")), ("حالة الأمر", wo.get("status")),
            ("القسم الطبي", wo.get("department")), ("مقدم البلاغ", wo.get("reported_by")),
            ("الفني/المهندس المكلف", wo.get("technician")), ("تاريخ الإنجاز", wo.get("completed_at"))
        ])

        content += '<h2 class="section">ثانيًا: بيانات الجهاز الطبي</h2>'
        content += self._html_info_table([
            ("رقم الأصل (Asset Tag)", eq.get("asset_number")), ("اسم الجهاز", eq.get("name_ar")),
            ("الرقم التسلسلي (S/N)", eq.get("serial_number")), ("الموديل", eq.get("model")),
            ("الأهمية", eq.get("criticality")), ("درجة الخطورة", eq.get("risk_level"))
        ])

        content += '<h2 class="section">ثالثًا: وصف العطل والإجراءات</h2>'
        content += '<div class="note-box"><strong>وصف العطل / البلاغ:</strong><br>' + self._html_value(wo.get("failure_description")) + '</div>'
        content += '<div class="note-box"><strong>الإجراءات التصحيحية / ملاحظات الإنجاز:</strong><br>' + self._html_value(wo.get("resolution_notes")) + '</div>'

        part_rows = [[p.get("part_number"), p.get("name"), p.get("quantity"),
                      p.get("unit_price", 0), p.get("total_price", 0)]
                     for p in report_data.get("parts", [])]
        content += '<h2 class="section">رابعًا: قطع الغيار المستخدمة</h2>'
        content += self._html_table(
            ["رقم القطعة", "اسم القطعة", "الكمية", "سعر الوحدة (ر.س)", "الإجمالي (ر.س)"],
            part_rows, "لم تُسجل قطع غيار مستخدمة في هذا الأمر"
        )

        content += '<h2 class="section">خامسًا: التكاليف</h2>'
        content += self._html_info_table([
            ("تكلفة قطع الغيار (ر.س)", wo.get("parts_cost", 0)),
            ("تكلفة العمالة (ر.س)", wo.get("labor_cost", 0)),
            ("إجمالي التكلفة (ر.س)", wo.get("total_cost", 0))
        ])
        content += """<table dir="rtl" class="signatures" width="100%" border="0" cellpadding="4" cellspacing="0" style="margin-top: 22pt; border-collapse: collapse;"><tbody><tr>
<td width="33.3%" align="center" style="vertical-align: top; padding: 12pt 8pt 4pt; border: none; border-top: 1pt solid #94A3B8;"><strong>الاعتماد الإداري</strong><br><br>التوقيع والختم: ........................</td>
<td width="33.3%" align="center" style="vertical-align: top; padding: 12pt 8pt 4pt; border: none; border-top: 1pt solid #94A3B8;"><strong>رئيس قسم الهندسة الطبية</strong><br><br>الاسم والتوقيع: ........................</td>
<td width="33.3%" align="center" style="vertical-align: top; padding: 12pt 8pt 4pt; border: none; border-top: 1pt solid #94A3B8;"><strong>الفني / المهندس المنفذ</strong><br><br>الاسم والتوقيع: ........................</td>
</tr></tbody></table>"""
        wo_num = wo.get("number")
        title = f"إشعار وتذكرة أمر صيانة طبية — رقم {wo_num}" if wo_num else "إشعار وتذكرة أمر صيانة طبية"
        return self._html_document(title, content, report_data)



report_service = ReportService()

