"""
Service for Corrective Maintenance Work Orders and Status workflows.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import or_
from src.models.work_order import WorkOrder, WorkOrderLog
from src.models.equipment import Equipment
from src.core.exceptions import ValidationError, NotFoundError
from src.core.permissions import check_permission, PERM_WORK_ORDER_CREATE, PERM_WORK_ORDER_EDIT
from src.services.audit_service import audit_service


class WorkOrderService:
    def get_work_orders(
        self,
        db: Session,
        search_query: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        department_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[WorkOrder]:
        query = db.query(WorkOrder)

        if status:
            query = query.filter(WorkOrder.status == status)
        if priority:
            query = query.filter(WorkOrder.priority == priority)
        if department_id:
            query = query.filter(WorkOrder.department_id == department_id)

        if search_query:
            term = f"%{search_query.strip()}%"
            query = query.filter(
                or_(
                    WorkOrder.work_order_number.ilike(term),
                    WorkOrder.failure_description.ilike(term),
                    WorkOrder.reported_by_name.ilike(term)
                )
            )

        return query.order_by(WorkOrder.id.desc()).offset(skip).limit(limit).all()

    def get_work_order_by_id(self, db: Session, wo_id: int) -> WorkOrder:
        wo = db.query(WorkOrder).filter_by(id=wo_id).first()
        if not wo:
            raise NotFoundError("WorkOrder", wo_id)
        return wo

    def create_work_order(self, db: Session, user, data: Dict[str, Any]) -> WorkOrder:
        check_permission(user, PERM_WORK_ORDER_CREATE)

        equipment_id = data.get("equipment_id")
        reported_by_name = data.get("reported_by_name", "").strip()
        failure_description = data.get("failure_description", "").strip()

        if not equipment_id or not reported_by_name or not failure_description:
            raise ValidationError("Equipment, Reported By, and Failure Description are required.")

        eq = db.query(Equipment).filter_by(id=equipment_id).first()
        if not eq:
            raise NotFoundError("Equipment", equipment_id)

        # Generate unique work order number safely
        year = datetime.now(timezone.utc).year
        prefix = f"WO-{year}-"
        latest = db.query(WorkOrder.work_order_number).filter(
            WorkOrder.work_order_number.like(f"{prefix}%")
        ).order_by(WorkOrder.id.desc()).first()
        seq = 1
        if latest and latest[0]:
            try:
                seq = int(latest[0].split("-")[-1]) + 1
            except (ValueError, IndexError):
                seq = db.query(WorkOrder).count() + 1
        else:
            seq = db.query(WorkOrder).count() + 1

        wo_number = f"{prefix}{seq:04d}"
        while db.query(WorkOrder).filter_by(work_order_number=wo_number).first():
            seq += 1
            wo_number = f"{prefix}{seq:04d}"

        wo = WorkOrder(
            work_order_number=wo_number,
            equipment_id=equipment_id,
            department_id=eq.department_id,
            reported_by_name=reported_by_name,
            reporter_contact=data.get("reporter_contact"),
            priority=data.get("priority", "medium"),
            failure_description=failure_description,
            symptoms=data.get("symptoms"),
            assigned_technician_id=data.get("assigned_technician_id"),
            status=data.get("status", "open")
        )
        db.add(wo)
        db.flush()

        # Update equipment status to under_maintenance if critical or high
        if wo.priority in ("critical", "high"):
            eq.status = "under_maintenance"

        # Log initial status transition
        log_entry = WorkOrderLog(
            work_order_id=wo.id,
            user_id=user.id,
            from_status=None,
            to_status=wo.status,
            notes=f"Work order created by {user.username}."
        )
        db.add(log_entry)
        db.flush()

        audit_service.log_action(
            db=db,
            action="CREATE",
            entity_name="WorkOrder",
            user_id=user.id,
            entity_id=str(wo.id),
            details=f"Created work order '{wo.work_order_number}' for equipment '{eq.name_ar}'."
        )
        return wo

    def update_work_order(self, db: Session, user, wo_id: int, data: Dict[str, Any]) -> WorkOrder:
        check_permission(user, PERM_WORK_ORDER_EDIT)
        wo = self.get_work_order_by_id(db, wo_id)

        old_status = wo.status
        new_status = data.get("status", old_status)

        for key in ("priority", "failure_description", "symptoms", "assigned_technician_id",
                    "diagnosis", "corrective_action", "failure_cause", "total_labor_cost", "total_parts_cost"):
            if key in data:
                setattr(wo, key, data[key])

        if new_status != old_status:
            wo.status = new_status
            if new_status in ("completed", "closed"):
                wo.completed_at = datetime.now(timezone.utc)
                if wo.equipment:
                    wo.equipment.status = "operational"
            elif new_status == "in_progress":
                wo.started_at = datetime.now(timezone.utc)

            log_entry = WorkOrderLog(
                work_order_id=wo.id,
                user_id=user.id,
                from_status=old_status,
                to_status=new_status,
                notes=data.get("status_notes", f"Status changed from {old_status} to {new_status}.")
            )
            db.add(log_entry)

        db.flush()
        return wo

    def get_work_order_statistics(self, db: Session) -> Dict[str, Any]:
        total = db.query(WorkOrder).count()
        open_orders = db.query(WorkOrder).filter(WorkOrder.status.in_(["open", "pending", "assigned"])).count()
        in_progress = db.query(WorkOrder).filter_by(status="in_progress").count()
        completed = db.query(WorkOrder).filter(WorkOrder.status.in_(["completed", "closed"])).count()
        urgent = db.query(WorkOrder).filter_by(priority="critical").count()

        return {
            "total": total,
            "open": open_orders,
            "in_progress": in_progress,
            "completed": completed,
            "urgent": urgent
        }

    get_statistics = get_work_order_statistics
    list_work_orders = get_work_orders


work_order_service = WorkOrderService()
