"""
Service for managing Vendors, Manufacturers, Suppliers, Maintenance Agents, and Vendor Support Engineers.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from src.models.vendor import Vendor, VendorEngineer
from src.core.exceptions import ValidationError, NotFoundError
from src.core.permissions import check_permission, PERM_VENDORS_MANAGE, PERM_VENDORS_VIEW
from src.services.audit_service import audit_service


class VendorService:
    def get_vendors(self, db: Session, vendor_type: Optional[str] = None) -> List[Vendor]:
        query = db.query(Vendor)
        if vendor_type and vendor_type != "all":
            query = query.filter_by(vendor_type=vendor_type)
        return query.order_by(Vendor.name.asc()).all()

    def get_vendor_by_id(self, db: Session, vendor_id: int) -> Vendor:
        vendor = db.query(Vendor).filter_by(id=vendor_id).first()
        if not vendor:
            raise NotFoundError("Vendor", vendor_id)
        return vendor

    def create_vendor(self, db: Session, user, data: Dict[str, Any]) -> Vendor:
        check_permission(user, PERM_VENDORS_MANAGE)
        name = data.get("name", "").strip()
        if not name:
            raise ValidationError("اسم الشركة أو المورد مطلوب.")

        vendor = Vendor(
            name=name,
            vendor_type=data.get("vendor_type", "supplier"),
            contact_person=data.get("contact_person"),
            phone=data.get("phone"),
            email=data.get("email"),
            address=data.get("address"),
            notes=data.get("notes")
        )
        db.add(vendor)
        db.commit()
        db.refresh(vendor)

        audit_service.log_action(
            db=db,
            action="CREATE",
            entity_name="Vendor",
            user_id=user.id if user else None,
            entity_id=str(vendor.id),
            details=f"إضافة جهة/شركة '{vendor.name}' (النوع: {vendor.vendor_type})"
        )
        return vendor

    def update_vendor(self, db: Session, user, vendor_id: int, data: Dict[str, Any]) -> Vendor:
        check_permission(user, PERM_VENDORS_MANAGE)
        vendor = self.get_vendor_by_id(db, vendor_id)
        for key in ("name", "vendor_type", "contact_person", "phone", "email", "address", "notes"):
            if key in data and data[key] is not None:
                setattr(vendor, key, data[key])
        db.commit()
        db.refresh(vendor)

        audit_service.log_action(
            db=db,
            action="UPDATE",
            entity_name="Vendor",
            user_id=user.id if user else None,
            entity_id=str(vendor.id),
            details=f"تعديل بيانات الجهة/الشركة '{vendor.name}'"
        )
        return vendor

    def delete_vendor(self, db: Session, user, vendor_id: int):
        check_permission(user, PERM_VENDORS_MANAGE)
        vendor = self.get_vendor_by_id(db, vendor_id)
        if vendor.supplied_equipment or vendor.manufactured_equipment or vendor.serviced_equipment:
            raise ValidationError("لا يمكن حذف الشركة لوجود أجهزة طبية مرتبطة بها في النظام.")
        if vendor.contracts:
            raise ValidationError("لا يمكن حذف الشركة لوجود عقود صيانة مرتبطة بها.")

        name = vendor.name
        db.delete(vendor)
        db.commit()

        audit_service.log_action(
            db=db,
            action="DELETE",
            entity_name="Vendor",
            user_id=user.id if user else None,
            entity_id=str(vendor_id),
            details=f"حذف الجهة/الشركة '{name}'"
        )

    # ── Vendor Engineers Management ──────────────────────────────────────────
    def add_engineer(self, db: Session, user, vendor_id: int, data: Dict[str, Any]) -> VendorEngineer:
        check_permission(user, PERM_VENDORS_MANAGE)
        vendor = self.get_vendor_by_id(db, vendor_id)

        name = (data.get("name") or "").strip()
        if not name:
            raise ValidationError("اسم مهندس الدعم مطلوب.")

        eng = VendorEngineer(
            vendor_id=vendor.id,
            name=name,
            phone=data.get("phone"),
            email=data.get("email"),
            specialization=data.get("specialization"),
            status=data.get("status", "active"),
            notes=data.get("notes")
        )
        db.add(eng)
        db.commit()
        db.refresh(eng)

        audit_service.log_action(
            db=db,
            user=user,
            action="ADD_VENDOR_ENGINEER",
            entity_name="VendorEngineer",
            entity_id=str(eng.id),
            details=f"إضافة مهندس دعم '{name}' للشركة '{vendor.name}'"
        )
        return eng

    def update_engineer(self, db: Session, user, engineer_id: int, data: Dict[str, Any]) -> VendorEngineer:
        check_permission(user, PERM_VENDORS_MANAGE)
        eng = db.query(VendorEngineer).filter_by(id=engineer_id).first()
        if not eng:
            raise NotFoundError("VendorEngineer", engineer_id)

        for key in ("name", "phone", "email", "specialization", "status", "notes"):
            if key in data and data[key] is not None:
                setattr(eng, key, data[key])

        db.commit()
        db.refresh(eng)

        audit_service.log_action(
            db=db,
            user=user,
            action="UPDATE_VENDOR_ENGINEER",
            entity_name="VendorEngineer",
            entity_id=str(eng.id),
            details=f"تعديل بيانات مهندس الدعم '{eng.name}'"
        )
        return eng

    def delete_engineer(self, db: Session, user, engineer_id: int) -> bool:
        check_permission(user, PERM_VENDORS_MANAGE)
        eng = db.query(VendorEngineer).filter_by(id=engineer_id).first()
        if not eng:
            raise NotFoundError("VendorEngineer", engineer_id)

        name = eng.name
        # Check if linked to any equipment
        from src.models.equipment import Equipment
        linked_eq = db.query(Equipment).filter_by(assigned_engineer_id=eng.id).first()
        if linked_eq:
            eng.status = "inactive"
            db.commit()
            details_str = f"تعطيل حساب مهندس الدعم '{name}' لوجود أجهزة مسندة إليه."
        else:
            db.delete(eng)
            db.commit()
            details_str = f"حذف مهندس الدعم '{name}'"

        audit_service.log_action(
            db=db,
            user=user,
            action="DELETE_VENDOR_ENGINEER",
            entity_name="VendorEngineer",
            entity_id=str(engineer_id),
            details=details_str
        )
        return True

    def get_vendor_engineers(self, db: Session, vendor_id: int) -> List[VendorEngineer]:
        return db.query(VendorEngineer).filter_by(vendor_id=vendor_id).order_by(VendorEngineer.name.asc()).all()

    def get_all_engineers(self, db: Session, active_only: bool = True) -> List[VendorEngineer]:
        query = db.query(VendorEngineer)
        if active_only:
            query = query.filter_by(status="active")
        return query.order_by(VendorEngineer.name.asc()).all()

    list_vendors = get_vendors
    add_vendor_engineer = add_engineer
    update_vendor_engineer = update_engineer
    delete_vendor_engineer = delete_engineer


vendor_service = VendorService()
