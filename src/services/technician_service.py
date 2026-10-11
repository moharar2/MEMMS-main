"""
Biomedical Technician and Clinical Engineer Service.
Manages technical personnel profiles, extended administrative data, qualifications,
experiences, and RBAC-protected compensation records.
"""
from typing import List, Optional, Dict, Any
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from src.models.technician import (
    Technician, TechnicianQualification,
    TechnicianExperience, TechnicianCompensation
)
from src.models.user import User
from src.services.audit_service import audit_service
from src.core.exceptions import ResourceNotFoundError, ValidationError
from src.core.permissions import (
    check_permission, PERM_TECHNICIANS_VIEW, PERM_TECHNICIANS_MANAGE,
    PERM_TECHNICIANS_SALARY_VIEW, PERM_TECHNICIANS_SALARY_MANAGE
)


class TechnicianService:
    @staticmethod
    def mask_id_number(id_num: Optional[str]) -> str:
        """Masks national ID/iqama for privacy in general views (e.g. *******1234)."""
        if not id_num or len(id_num.strip()) < 4:
            return "—"
        clean = id_num.strip()
        return ("*" * (len(clean) - 4)) + clean[-4:]

    @staticmethod
    def create_technician(
        db: Session,
        employee_id: str,
        full_name: str,
        specialization: str,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        qualification: Optional[str] = None,
        status: str = "active",
        user_id: Optional[int] = None,
        operator_user_id: Optional[int] = None,
        nationality: Optional[str] = None,
        id_document_type: Optional[str] = "national_id",
        id_number: Optional[str] = None,
        job_title: Optional[str] = None,
        department_id: Optional[int] = None,
        work_entity: Optional[str] = None,
        hire_date: Optional[date] = None
    ) -> Technician:
        """Create a new engineering staff member."""
        if not employee_id or not employee_id.strip():
            raise ValidationError("الرقم الوظيفي مطلوب.")
        if not full_name or not full_name.strip():
            raise ValidationError("الاسم الكامل مطلوب.")
        if not specialization or not specialization.strip():
            raise ValidationError("التخصص الهندسي مطلوب.")

        existing = db.query(Technician).filter(Technician.employee_id == employee_id.strip()).first()
        if existing:
            raise ValidationError(f"الرقم الوظيفي '{employee_id}' مسجل مسبقاً لموظف آخر.")

        tech = Technician(
            employee_id=employee_id.strip(),
            full_name=full_name.strip(),
            specialization=specialization.strip(),
            phone=phone.strip() if phone else None,
            email=email.strip() if email else None,
            qualification=qualification.strip() if qualification else None,
            user_id=user_id,
            status=status or "active",
            nationality=nationality.strip() if nationality else None,
            id_document_type=id_document_type or "national_id",
            id_number=id_number.strip() if id_number else None,
            job_title=job_title.strip() if job_title else None,
            department_id=department_id,
            work_entity=work_entity.strip() if work_entity else None,
            hire_date=hire_date
        )
        db.add(tech)
        db.commit()
        db.refresh(tech)

        audit_service.log_action(
            db=db,
            action="CREATE",
            entity_name="Technician",
            user_id=operator_user_id,
            entity_id=str(tech.id),
            details=f"إضافة كادر فني/مهندس '{tech.full_name}' ({tech.employee_id})"
        )
        return tech

    @staticmethod
    def update_technician(
        db: Session,
        tech_id: int,
        operator_user_id: Optional[int] = None,
        **kwargs
    ) -> Technician:
        """Update technician profile."""
        tech = db.query(Technician).filter(Technician.id == tech_id).first()
        if not tech:
            raise ResourceNotFoundError(f"Technician with ID {tech_id} not found")

        for k, v in kwargs.items():
            if hasattr(tech, k) and v is not None:
                setattr(tech, k, v)

        db.commit()
        db.refresh(tech)

        audit_service.log_action(
            db=db,
            action="UPDATE",
            entity_name="Technician",
            user_id=operator_user_id,
            entity_id=str(tech.id),
            details=f"تحديث بيانات الموظف/المهندس '{tech.full_name}'"
        )
        return tech

    @staticmethod
    def delete_technician(db: Session, tech_id: int, operator_user_id: Optional[int] = None) -> bool:
        """Deactivate technician without breaking historical logs."""
        tech = db.query(Technician).filter(Technician.id == tech_id).first()
        if not tech:
            raise ResourceNotFoundError(f"Technician with ID {tech_id} not found")

        name = tech.full_name
        tech.status = "inactive"
        db.commit()

        audit_service.log_action(
            db=db,
            action="DELETE",
            entity_name="Technician",
            user_id=operator_user_id,
            entity_id=str(tech_id),
            details=f"تعطيل حساب الفني/المهندس '{name}'"
        )
        return True

    @staticmethod
    def list_technicians(
        db: Session,
        status: Optional[str] = None,
        specialization: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Technician]:
        """List technicians with filtering."""
        query = db.query(Technician)
        if status and status != "all":
            query = query.filter(Technician.status == status)
        if specialization and specialization != "all":
            query = query.filter(Technician.specialization == specialization)
        if search:
            s = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Technician.employee_id.ilike(s),
                    Technician.full_name.ilike(s),
                    Technician.specialization.ilike(s),
                    Technician.email.ilike(s)
                )
            )
        return query.order_by(Technician.full_name.asc()).all()

    @staticmethod
    def get_technician_by_id(db: Session, tech_id: int) -> Technician:
        tech = db.query(Technician).filter_by(id=tech_id).first()
        if not tech:
            raise ResourceNotFoundError(f"Technician with ID {tech_id} not found")
        return tech

    # ── Qualifications & Certificates ─────────────────────────────────────────
    @staticmethod
    def add_qualification(db: Session, user, tech_id: int, data: Dict[str, Any]) -> TechnicianQualification:
        check_permission(user, PERM_TECHNICIANS_MANAGE)
        tech = TechnicianService.get_technician_by_id(db, tech_id)

        name = (data.get("name") or "").strip()
        if not name:
            raise ValidationError("اسم المؤهل أو الشهادة مطلوب.")

        qual = TechnicianQualification(
            technician_id=tech.id,
            name=name,
            specialization=data.get("specialization"),
            issuing_organization=data.get("issuing_organization"),
            issue_date=data.get("issue_date"),
            expiry_date=data.get("expiry_date"),
            notes=data.get("notes"),
            attachment_path=data.get("attachment_path")
        )
        db.add(qual)
        db.commit()
        db.refresh(qual)

        audit_service.log_action(
            db=db,
            user=user,
            action="ADD_QUALIFICATION",
            entity_name="Technician",
            entity_id=str(tech.id),
            details=f"إضافة مؤهل/شهادة '{name}' للموظف '{tech.full_name}'"
        )
        return qual

    @staticmethod
    def delete_qualification(db: Session, user, qual_id: int) -> bool:
        check_permission(user, PERM_TECHNICIANS_MANAGE)
        qual = db.query(TechnicianQualification).filter_by(id=qual_id).first()
        if not qual:
            raise ResourceNotFoundError("Qualification not found")

        tech_id = qual.technician_id
        name = qual.name
        db.delete(qual)
        db.commit()

        audit_service.log_action(
            db=db,
            user=user,
            action="DELETE_QUALIFICATION",
            entity_name="Technician",
            entity_id=str(tech_id),
            details=f"حذف مؤهل '{name}' للموظف رقم {tech_id}"
        )
        return True

    @staticmethod
    def get_qualifications(db: Session, tech_id: int) -> List[TechnicianQualification]:
        return db.query(TechnicianQualification).filter_by(technician_id=tech_id).order_by(TechnicianQualification.id.asc()).all()

    # ── Professional Experiences ──────────────────────────────────────────────
    @staticmethod
    def add_experience(db: Session, user, tech_id: int, data: Dict[str, Any]) -> TechnicianExperience:
        check_permission(user, PERM_TECHNICIANS_MANAGE)
        tech = TechnicianService.get_technician_by_id(db, tech_id)

        employer = (data.get("previous_employer") or "").strip()
        title = (data.get("job_title") or "").strip()
        start_date = data.get("start_date")
        if not employer or not title or not start_date:
            raise ValidationError("جهة العمل السابقة، المسمى الوظيفي، وتاريخ البداية حقول إلزامية.")

        exp = TechnicianExperience(
            technician_id=tech.id,
            previous_employer=employer,
            job_title=title,
            specialization=data.get("specialization"),
            start_date=start_date,
            end_date=data.get("end_date"),
            task_description=data.get("task_description")
        )
        db.add(exp)
        db.commit()
        db.refresh(exp)

        audit_service.log_action(
            db=db,
            user=user,
            action="ADD_EXPERIENCE",
            entity_name="Technician",
            entity_id=str(tech.id),
            details=f"إضافة خبرة مهنية لدى '{employer}' للموظف '{tech.full_name}'"
        )
        return exp

    @staticmethod
    def delete_experience(db: Session, user, exp_id: int) -> bool:
        check_permission(user, PERM_TECHNICIANS_MANAGE)
        exp = db.query(TechnicianExperience).filter_by(id=exp_id).first()
        if not exp:
            raise ResourceNotFoundError("Experience not found")

        tech_id = exp.technician_id
        employer = exp.previous_employer
        db.delete(exp)
        db.commit()

        audit_service.log_action(
            db=db,
            user=user,
            action="DELETE_EXPERIENCE",
            entity_name="Technician",
            entity_id=str(tech_id),
            details=f"حذف خبرة سابقة لدى '{employer}' للموظف رقم {tech_id}"
        )
        return True

    @staticmethod
    def get_experiences(db: Session, tech_id: int) -> List[TechnicianExperience]:
        return db.query(TechnicianExperience).filter_by(technician_id=tech_id).order_by(TechnicianExperience.start_date.desc()).all()

    # ── Salary & Allowances (Protected Financial Records) ─────────────────────
    @staticmethod
    def get_compensation(db: Session, user, tech_id: int) -> Optional[TechnicianCompensation]:
        check_permission(user, PERM_TECHNICIANS_SALARY_VIEW)
        return db.query(TechnicianCompensation).filter_by(technician_id=tech_id).order_by(TechnicianCompensation.effective_date.desc()).first()

    @staticmethod
    def set_compensation(db: Session, user, tech_id: int, data: Dict[str, Any]) -> TechnicianCompensation:
        check_permission(user, PERM_TECHNICIANS_SALARY_MANAGE)
        tech = TechnicianService.get_technician_by_id(db, tech_id)

        basic_salary = float(data.get("basic_salary", 0.0) or 0.0)
        allowances = float(data.get("allowances", 0.0) or 0.0)
        if basic_salary < 0 or allowances < 0:
            raise ValidationError("الراتب والبدلات لا يمكن أن تكون بقيم سالبة.")

        total_package = round(basic_salary + allowances, 2)
        effective_date = data.get("effective_date") or date.today()

        comp = db.query(TechnicianCompensation).filter_by(technician_id=tech.id).first()
        if not comp:
            comp = TechnicianCompensation(technician_id=tech.id)
            db.add(comp)

        comp.basic_salary = basic_salary
        comp.allowances = allowances
        comp.allowance_type = data.get("allowance_type")
        comp.total_package = total_package
        comp.effective_date = effective_date
        comp.notes = data.get("notes")

        db.commit()
        db.refresh(comp)

        audit_service.log_action(
            db=db,
            user=user,
            action="UPDATE_SALARY",
            entity_name="Technician",
            entity_id=str(tech.id),
            details=f"تحديث البيانات المالية والراتب للموظف '{tech.full_name}' (الإجمالي: {total_package:,.2f} ر.س)"
        )
        return comp

    @staticmethod
    def get_technician_statistics(db: Session) -> Dict[str, int]:
        """Compute staff KPIs."""
        total = db.query(func.count(Technician.id)).scalar() or 0
        active = db.query(func.count(Technician.id)).filter(Technician.status == "active").scalar() or 0
        on_leave = db.query(func.count(Technician.id)).filter(Technician.status == "on_leave").scalar() or 0

        return {
            "total": total,
            "total_technicians": total,
            "active": active,
            "on_leave": on_leave
        }


technician_service = TechnicianService()
