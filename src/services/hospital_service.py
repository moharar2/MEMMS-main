"""
Service for managing Hospitals, Departments, and Location rooms.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from src.models.hospital import Hospital, Department, Location
from src.core.exceptions import ValidationError, NotFoundError
from src.core.permissions import check_permission, PERM_DEPARTMENTS_MANAGE, PERM_DEPARTMENTS_VIEW
from src.services.audit_service import audit_service


class HospitalService:
    # --- Hospital ---
    def get_hospitals(self, db: Session) -> List[Hospital]:
        return db.query(Hospital).filter_by(is_active=True).all()

    def get_or_create_default_hospital(self, db: Session) -> Hospital:
        hospital = db.query(Hospital).first()
        if not hospital:
            hospital = Hospital(
                name_ar="مستشفى الأمل التخصصي",
                name_en="Al-Amal Specialized Hospital",
                code="HOSP-01",
                address="الرياض، المملكة العربية السعودية",
                phone="0110000000",
                is_active=True
            )
            db.add(hospital)
            db.flush()
        return hospital

    # --- Department ---
    def get_departments(self, db: Session, hospital_id: Optional[int] = None) -> List[Department]:
        query = db.query(Department).filter_by(is_active=True)
        if hospital_id:
            query = query.filter_by(hospital_id=hospital_id)
        return query.order_by(Department.name_ar.asc()).all()

    def get_department_by_id(self, db: Session, dept_id: int) -> Department:
        dept = db.query(Department).filter_by(id=dept_id).first()
        if not dept:
            raise NotFoundError("Department", dept_id)
        return dept

    def create_department(self, db: Session, user, data: Dict[str, Any]) -> Department:
        check_permission(user, PERM_DEPARTMENTS_MANAGE)
        name_ar = data.get("name_ar", "").strip()
        code = data.get("code", "").strip()
        if not name_ar or not code:
            raise ValidationError("Department Arabic name and code are required.")

        hospital_id = data.get("hospital_id")
        if not hospital_id:
            default_hosp = self.get_or_create_default_hospital(db)
            hospital_id = default_hosp.id

        dept = Department(
            hospital_id=hospital_id,
            name_ar=name_ar,
            name_en=data.get("name_en", name_ar).strip(),
            code=code,
            floor=data.get("floor"),
            is_active=data.get("is_active", True)
        )
        db.add(dept)
        db.flush()

        audit_service.log_action(
            db=db,
            action="CREATE",
            entity_name="Department",
            user_id=user.id,
            entity_id=str(dept.id),
            details=f"Created department '{dept.name_ar}' ({dept.code})."
        )
        return dept

    def update_department(self, db: Session, user, dept_id: int, data: Dict[str, Any]) -> Department:
        check_permission(user, PERM_DEPARTMENTS_MANAGE)
        dept = self.get_department_by_id(db, dept_id)
        for key in ("name_ar", "name_en", "code", "floor", "is_active"):
            if key in data:
                setattr(dept, key, data[key])
        db.flush()

        audit_service.log_action(
            db=db,
            action="UPDATE",
            entity_name="Department",
            user_id=user.id,
            entity_id=str(dept.id),
            details=f"Updated department '{dept.name_ar}'."
        )
        return dept

    def delete_department(self, db: Session, user, dept_id: int):
        check_permission(user, PERM_DEPARTMENTS_MANAGE)
        dept = self.get_department_by_id(db, dept_id)
        if dept.equipment:
            raise ValidationError("Cannot delete department with associated medical equipment.")
        dept.is_active = False
        db.flush()

        audit_service.log_action(
            db=db,
            action="DELETE",
            entity_name="Department",
            user_id=user.id,
            entity_id=str(dept.id),
            details=f"Deactivated department '{dept.name_ar}'."
        )

    # --- Location ---
    def get_locations(self, db: Session, department_id: Optional[int] = None) -> List[Location]:
        query = db.query(Location)
        if department_id:
            query = query.filter_by(department_id=department_id)
        return query.order_by(Location.room_number.asc()).all()

    def create_location(self, db: Session, user, data: Dict[str, Any]) -> Location:
        check_permission(user, PERM_DEPARTMENTS_MANAGE)
        room_number = data.get("room_number", "").strip()
        room_name = data.get("room_name", "").strip()
        dept_id = data.get("department_id")

        if not room_number or not room_name or not dept_id:
            raise ValidationError("Room number, name, and department are required.")

        loc = Location(
            department_id=dept_id,
            room_number=room_number,
            room_name=room_name,
            description=data.get("description")
        )
        db.add(loc)
        db.flush()
        return loc

    def get_rooms(self, db: Session, department_id: Optional[int] = None) -> List[Location]:
        return self.get_locations(db, department_id=department_id)


hospital_service = HospitalService()
