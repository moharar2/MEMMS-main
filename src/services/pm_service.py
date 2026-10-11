"""
Preventive Maintenance Service.
Manages PM plans, recurring schedule generation, overdue detection,
and PM execution recording with automatic next-schedule generation.
"""
from datetime import date, datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from src.models.preventive import PMPlan, PMSchedule, PMExecution
from src.models.equipment import Equipment
from src.models.technician import Technician
from src.services.audit_service import audit_service
from src.core.exceptions import ResourceNotFoundError, ValidationError


class PMService:
    @staticmethod
    def create_pm_plan(
        db: Session,
        title: str,
        frequency_days: int,
        checklist_template: List[str],
        estimated_duration_minutes: int = 60,
        equipment_id: Optional[int] = None,
        category: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> PMPlan:
        """Create a new PM Plan / Protocol."""
        if not title or not title.strip():
            raise ValidationError("Protocol title is required")
        if frequency_days <= 0:
            raise ValidationError("Frequency days must be positive")
        if not equipment_id and not category:
            raise ValidationError("PM Plan must be assigned to an equipment or category")

        plan = PMPlan(
            title=title.strip(),
            frequency_days=frequency_days,
            checklist_template=checklist_template or [],
            estimated_duration_minutes=estimated_duration_minutes,
            equipment_id=equipment_id,
            category=category,
            is_active=True
        )
        db.add(plan)
        db.commit()
        db.refresh(plan)

        audit_service.log(
            db,
            action="CREATE",
            entity_type="PMPlan",
            entity_id=plan.id,
            user_id=user_id,
            details=f"Created PM Plan '{plan.title}' ({frequency_days}d)"
        )
        return plan

    @staticmethod
    def update_pm_plan(
        db: Session,
        plan_id: int,
        user_id: Optional[int] = None,
        **kwargs
    ) -> PMPlan:
        """Update an existing PM Plan."""
        plan = db.query(PMPlan).filter(PMPlan.id == plan_id).first()
        if not plan:
            raise ResourceNotFoundError(f"PM Plan with ID {plan_id} not found")

        for k, v in kwargs.items():
            if hasattr(plan, k) and v is not None:
                setattr(plan, k, v)

        db.commit()
        db.refresh(plan)

        audit_service.log(
            db,
            action="UPDATE",
            entity_type="PMPlan",
            entity_id=plan.id,
            user_id=user_id,
            details=f"Updated PM Plan '{plan.title}'"
        )
        return plan

    @staticmethod
    def delete_pm_plan(db: Session, plan_id: int, user_id: Optional[int] = None) -> bool:
        """Delete a PM plan and related schedules."""
        plan = db.query(PMPlan).filter(PMPlan.id == plan_id).first()
        if not plan:
            raise ResourceNotFoundError(f"PM Plan with ID {plan_id} not found")

        title = plan.title
        db.delete(plan)
        db.commit()

        audit_service.log(
            db,
            action="DELETE",
            entity_type="PMPlan",
            entity_id=plan_id,
            user_id=user_id,
            details=f"Deleted PM Plan '{title}'"
        )
        return True

    @staticmethod
    def get_pm_plan(db: Session, plan_id: int) -> Optional[PMPlan]:
        return db.query(PMPlan).filter(PMPlan.id == plan_id).first()

    @staticmethod
    def list_pm_plans(
        db: Session,
        active_only: bool = True,
        category: Optional[str] = None,
        equipment_id: Optional[int] = None
    ) -> List[PMPlan]:
        """List PM plans with optional filtering."""
        query = db.query(PMPlan)
        if active_only:
            query = query.filter(PMPlan.is_active.is_(True))
        if category:
            query = query.filter(PMPlan.category == category)
        if equipment_id:
            query = query.filter(
                or_(
                    PMPlan.equipment_id == equipment_id,
                    PMPlan.category.in_(
                        db.query(Equipment.category).filter(Equipment.id == equipment_id)
                    )
                )
            )
        return query.order_by(PMPlan.title.asc()).all()

    @staticmethod
    def generate_schedules_for_plan(
        db: Session,
        plan_id: int,
        base_date: Optional[date] = None
    ) -> List[PMSchedule]:
        """Generate PM schedule entries for target equipment."""
        plan = db.query(PMPlan).filter(PMPlan.id == plan_id).first()
        if not plan or not plan.is_active:
            return []

        target_date = base_date or date.today()
        due_date = target_date + timedelta(days=plan.frequency_days)

        # Determine target equipment
        target_equipment_ids = []
        if plan.equipment_id:
            target_equipment_ids.append(plan.equipment_id)
        elif plan.category:
            eqs = db.query(Equipment.id).filter(
                Equipment.category == plan.category,
                Equipment.status.in_(["operational", "standby", "under_maintenance"])
            ).all()
            target_equipment_ids = [e[0] for e in eqs]

        new_schedules = []
        for eq_id in target_equipment_ids:
            # Check if active schedule exists
            existing = db.query(PMSchedule).filter(
                PMSchedule.pm_plan_id == plan.id,
                PMSchedule.equipment_id == eq_id,
                PMSchedule.status.in_(["scheduled", "overdue"])
            ).first()

            if not existing:
                schedule = PMSchedule(
                    pm_plan_id=plan.id,
                    equipment_id=eq_id,
                    due_date=due_date,
                    status="scheduled"
                )
                db.add(schedule)
                new_schedules.append(schedule)

        if new_schedules:
            db.commit()
            for s in new_schedules:
                db.refresh(s)

        return new_schedules

    @staticmethod
    def auto_update_overdue_schedules(db: Session) -> int:
        """Mark scheduled tasks whose due_date is in the past as overdue."""
        today = date.today()
        try:
            updated_count = db.query(PMSchedule).filter(
                PMSchedule.status == "scheduled",
                PMSchedule.due_date < today
            ).update({"status": "overdue"}, synchronize_session=False)

            if updated_count > 0:
                db.commit()
            return updated_count
        except Exception:
            # If database is locked or any transient error, skip gracefully
            try:
                db.rollback()
            except Exception:
                pass
            return 0

    @staticmethod
    def list_schedules(
        db: Session,
        status: Optional[str] = None,
        equipment_id: Optional[int] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> List[PMSchedule]:
        """List PM schedules with auto-overdue synchronization and filtering."""
        PMService.auto_update_overdue_schedules(db)

        query = db.query(PMSchedule)
        if status and status != "all":
            query = query.filter(PMSchedule.status == status)
        if equipment_id:
            query = query.filter(PMSchedule.equipment_id == equipment_id)
        if from_date:
            query = query.filter(PMSchedule.due_date >= from_date)
        if to_date:
            query = query.filter(PMSchedule.due_date <= to_date)

        return query.order_by(PMSchedule.due_date.asc()).all()

    @staticmethod
    def record_pm_execution(
        db: Session,
        schedule_id: int,
        technician_id: int,
        passed: bool,
        results_summary: Optional[str] = None,
        measurements: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None,
        execution_date: Optional[datetime] = None,
        user_id: Optional[int] = None
    ) -> PMExecution:
        """Record PM execution findings and automatically schedule next inspection."""
        schedule = db.query(PMSchedule).filter(PMSchedule.id == schedule_id).first()
        if not schedule:
            raise ResourceNotFoundError(f"PM Schedule with ID {schedule_id} not found")

        tech = db.query(Technician).filter(Technician.id == technician_id).first()
        if not tech:
            raise ValidationError(f"Technician with ID {technician_id} does not exist")

        now_utc = execution_date or datetime.now(timezone.utc)
        exec_date_only = now_utc.date() if isinstance(now_utc, datetime) else now_utc

        # Calculate next due date from the plan's frequency
        plan = schedule.plan
        freq_days = plan.frequency_days if plan else 90
        next_due = exec_date_only + timedelta(days=freq_days)

        execution = PMExecution(
            pm_schedule_id=schedule.id,
            equipment_id=schedule.equipment_id,
            technician_id=technician_id,
            execution_date=now_utc,
            completion_date=now_utc,
            passed=passed,
            results_summary=results_summary or "",
            measurements=measurements or {},
            notes=notes or "",
            next_due_date=next_due
        )
        db.add(execution)

        # Mark current schedule as completed
        schedule.status = "completed"

        # Auto-create next recurring schedule if plan is active
        if plan and plan.is_active:
            next_schedule = PMSchedule(
                pm_plan_id=plan.id,
                equipment_id=schedule.equipment_id,
                due_date=next_due,
                status="scheduled"
            )
            db.add(next_schedule)

        db.commit()
        db.refresh(execution)

        audit_service.log(
            db,
            action="PM_EXECUTION",
            entity_type="PMExecution",
            entity_id=execution.id,
            user_id=user_id,
            details=f"Recorded PM for Equipment #{schedule.equipment_id} (Passed: {passed})"
        )
        return execution

    @staticmethod
    def get_pm_statistics(db: Session) -> Dict[str, int]:
        """Compute summary PM KPI metrics."""
        PMService.auto_update_overdue_schedules(db)
        today = date.today()
        first_of_month = date(today.year, today.month, 1)

        total_schedules = db.query(func.count(PMSchedule.id)).scalar() or 0
        scheduled_count = db.query(func.count(PMSchedule.id)).filter(PMSchedule.status == "scheduled").scalar() or 0
        overdue_count = db.query(func.count(PMSchedule.id)).filter(PMSchedule.status == "overdue").scalar() or 0
        
        completed_this_month = db.query(func.count(PMExecution.id)).filter(
            PMExecution.execution_date >= datetime(first_of_month.year, first_of_month.month, 1, tzinfo=timezone.utc)
        ).scalar() or 0

        return {
            "total_schedules": total_schedules,
            "scheduled": scheduled_count,
            "overdue": overdue_count,
            "completed_this_month": completed_this_month
        }

    list_plans = list_pm_plans
    list_pm_schedules = list_schedules


pm_service = PMService()
