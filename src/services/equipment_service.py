"""
Service for Medical Equipment lifecycle, transfers, status management, and statistics.
"""
from typing import List, Optional, Dict, Any
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import or_
from src.models.equipment import Equipment, EquipmentTransfer, EquipmentAccessory, EquipmentReceiving
from src.models.hospital import Department, Location
from src.core.exceptions import ValidationError, NotFoundError, DuplicateRecordError
from src.core.permissions import (
    check_permission, PERM_EQUIPMENT_VIEW, PERM_EQUIPMENT_CREATE,
    PERM_EQUIPMENT_EDIT, PERM_EQUIPMENT_DELETE,
    PERM_ACCESSORIES_MANAGE, PERM_RECEIVING_MANAGE
)
from src.services.audit_service import audit_service


class EquipmentService:
    def get_equipment_list(
        self,
        db: Session,
        search_query: Optional[str] = None,
        department_id: Optional[int] = None,
        status: Optional[str] = None,
        category: Optional[str] = None,
        risk_level: Optional[str] = None,
        skip: int = 0,
        limit: int = 200
    ) -> List[Equipment]:
        query = db.query(Equipment)

        if department_id:
            query = query.filter(Equipment.department_id == department_id)
        if status:
            query = query.filter(Equipment.status == status)
        if category:
            query = query.filter(Equipment.category == category)
        if risk_level:
            query = query.filter(Equipment.risk_level == risk_level)

        if search_query:
            term = f"%{search_query.strip()}%"
            query = query.filter(
                or_(
                    Equipment.name_ar.ilike(term),
                    Equipment.name_en.ilike(term),
                    Equipment.asset_number.ilike(term),
                    Equipment.serial_number.ilike(term),
                    Equipment.model.ilike(term),
                    Equipment.category.ilike(term)
                )
            )

        return query.order_by(Equipment.id.desc()).offset(skip).limit(limit).all()

    def get_equipment_by_id(self, db: Session, eq_id: int) -> Equipment:
        eq = db.query(Equipment).filter_by(id=eq_id).first()
        if not eq:
            raise NotFoundError("Equipment", eq_id)
        return eq

    def create_equipment(self, db: Session, user, data: Dict[str, Any]) -> Equipment:
        check_permission(user, PERM_EQUIPMENT_CREATE)

        asset_number = data.get("asset_number", "").strip()
        serial_number = data.get("serial_number", "").strip()
        name_ar = data.get("name_ar", "").strip()
        department_id = data.get("department_id")

        if not asset_number or not serial_number or not name_ar or not department_id:
            raise ValidationError("Asset number, Serial number, Arabic name, and Department are required.")

        # Check uniqueness
        if db.query(Equipment).filter_by(asset_number=asset_number).first():
            raise DuplicateRecordError(f"Equipment with asset number '{asset_number}' already exists.")
        if db.query(Equipment).filter_by(serial_number=serial_number).first():
            raise DuplicateRecordError(f"Equipment with serial number '{serial_number}' already exists.")

        eq = Equipment(
            asset_number=asset_number,
            inventory_number=data.get("inventory_number"),
            serial_number=serial_number,
            name_ar=name_ar,
            name_en=data.get("name_en", name_ar).strip(),
            model=data.get("model"),
            category=data.get("category", "General"),
            manufacturer_id=data.get("manufacturer_id"),
            supplier_id=data.get("supplier_id"),
            agent_id=data.get("agent_id"),
            assigned_engineer_id=data.get("assigned_engineer_id"),
            department_id=department_id,
            location_id=data.get("location_id"),
            purchase_date=data.get("purchase_date"),
            installation_date=data.get("installation_date"),
            warranty_expiry_date=data.get("warranty_expiry_date"),
            purchase_price=float(data.get("purchase_price", 0.0) or 0.0),
            status=data.get("status", "operational"),
            risk_level=data.get("risk_level", "medium"),
            criticality=data.get("criticality", "semi_critical"),
            notes=data.get("notes")
        )
        db.add(eq)
        db.flush()

        audit_service.log_action(
            db=db,
            action="CREATE",
            entity_name="Equipment",
            user_id=user.id,
            entity_id=str(eq.id),
            details=f"Added equipment '{eq.name_ar}' (Asset: {eq.asset_number}, S/N: {eq.serial_number})."
        )
        return eq

    def update_equipment(self, db: Session, user, eq_id: int, data: Dict[str, Any]) -> Equipment:
        check_permission(user, PERM_EQUIPMENT_EDIT)
        eq = self.get_equipment_by_id(db, eq_id)

        # Check asset number uniqueness if changed
        new_asset = data.get("asset_number")
        if new_asset and new_asset != eq.asset_number:
            if db.query(Equipment).filter(Equipment.asset_number == new_asset, Equipment.id != eq_id).first():
                raise DuplicateRecordError(f"Asset number '{new_asset}' already belongs to another device.")

        # Check serial number uniqueness if changed
        new_serial = data.get("serial_number")
        if new_serial and new_serial != eq.serial_number:
            if db.query(Equipment).filter(Equipment.serial_number == new_serial, Equipment.id != eq_id).first():
                raise DuplicateRecordError(f"Serial number '{new_serial}' already belongs to another device.")

        old_values = eq.to_dict()

        for key, val in data.items():
            if hasattr(eq, key) and key not in ("id", "created_at", "updated_at"):
                setattr(eq, key, val)

        db.flush()

        audit_service.log_action(
            db=db,
            action="UPDATE",
            entity_name="Equipment",
            user_id=user.id,
            entity_id=str(eq.id),
            details=f"Updated equipment '{eq.name_ar}' (Asset: {eq.asset_number}).",
            old_values=old_values,
            new_values=eq.to_dict()
        )
        return eq

    def delete_equipment(self, db: Session, user, eq_id: int):
        check_permission(user, PERM_EQUIPMENT_DELETE)
        eq = self.get_equipment_by_id(db, eq_id)

        # Check if work orders exist
        if eq.work_orders:
            raise ValidationError("Cannot delete equipment that has existing work order history.")

        asset_num = eq.asset_number
        name = eq.name_ar
        db.delete(eq)
        db.flush()

        audit_service.log_action(
            db=db,
            action="DELETE",
            entity_name="Equipment",
            user_id=user.id,
            entity_id=str(eq_id),
            details=f"Deleted equipment '{name}' (Asset: {asset_num})."
        )

    def transfer_equipment(
        self,
        db: Session,
        user,
        eq_id: int,
        to_department_id: int,
        to_location_id: Optional[int] = None,
        reason: Optional[str] = None
    ) -> EquipmentTransfer:
        """Transfers equipment from its current department/location to a new one and records history."""
        check_permission(user, PERM_EQUIPMENT_EDIT)
        eq = self.get_equipment_by_id(db, eq_id)

        from_dept_id = eq.department_id
        from_loc_id = eq.location_id

        if from_dept_id == to_department_id and from_loc_id == to_location_id:
            raise ValidationError("Device is already at the selected department and location.")

        # Create transfer record
        transfer = EquipmentTransfer(
            equipment_id=eq.id,
            from_department_id=from_dept_id,
            to_department_id=to_department_id,
            from_location_id=from_loc_id,
            to_location_id=to_location_id,
            transfer_date=date.today(),
            reason=reason,
            transferred_by_user_id=user.id
        )
        db.add(transfer)

        # Update equipment current location
        eq.department_id = to_department_id
        eq.location_id = to_location_id
        db.flush()

        audit_service.log_action(
            db=db,
            action="TRANSFER",
            entity_name="Equipment",
            user_id=user.id,
            entity_id=str(eq.id),
            details=f"Transferred equipment '{eq.name_ar}' from dept {from_dept_id} to dept {to_department_id}. Reason: {reason or 'N/A'}"
        )
        return transfer

    def get_equipment_stats(self, db: Session) -> Dict[str, int]:
        """Calculates equipment KPI counts."""
        total = db.query(Equipment).count()
        operational = db.query(Equipment).filter_by(status="operational").count()
        under_maintenance = db.query(Equipment).filter_by(status="under_maintenance").count()
        out_of_service = db.query(Equipment).filter_by(status="out_of_service").count()
        scrapped = db.query(Equipment).filter_by(status="scrapped").count()
        standby = db.query(Equipment).filter_by(status="standby").count()
        high_risk = db.query(Equipment).filter_by(risk_level="high").count()

        return {
            "total": total,
            "operational": operational,
            "under_maintenance": under_maintenance,
            "out_of_service": out_of_service,
            "scrapped": scrapped,
            "standby": standby,
            "high_risk": high_risk
        }

    # ── Accessories Management ───────────────────────────────────────────────
    def add_accessory(self, db: Session, user, equipment_id: int, data: Dict[str, Any]) -> EquipmentAccessory:
        check_permission(user, PERM_ACCESSORIES_MANAGE)
        eq = self.get_equipment_by_id(db, equipment_id)

        name = (data.get("name") or "").strip()
        if not name:
            raise ValidationError("اسم الملحق مطلوب.")

        quantity = float(data.get("quantity", 1.0) or 1.0)
        unit_cost = float(data.get("unit_cost", 0.0) or 0.0)
        if quantity <= 0:
            raise ValidationError("الكمية يجب أن تكون أكبر من الصفر.")
        if unit_cost < 0:
            raise ValidationError("تكلفة الوحدة لا يمكن أن تكون سالبة.")

        total_cost = round(quantity * unit_cost, 2)

        accessory = EquipmentAccessory(
            equipment_id=eq.id,
            name=name,
            model_number=data.get("model_number"),
            serial_number=data.get("serial_number"),
            manufacturer=data.get("manufacturer"),
            quantity=quantity,
            unit_cost=unit_cost,
            total_cost=total_cost,
            added_date=data.get("added_date") or date.today(),
            notes=data.get("notes")
        )
        db.add(accessory)
        db.commit()
        db.refresh(accessory)

        audit_service.log_action(
            db=db,
            user=user,
            action="ADD_ACCESSORY",
            entity_name="Equipment",
            entity_id=str(eq.id),
            details=f"إضافة ملحق '{name}' (كمية: {quantity:g}, إجمالي: {total_cost:,.2f}) للجهاز {eq.asset_number}"
        )
        return accessory

    def update_accessory(self, db: Session, user, accessory_id: int, data: Dict[str, Any]) -> EquipmentAccessory:
        check_permission(user, PERM_ACCESSORIES_MANAGE)
        accessory = db.query(EquipmentAccessory).filter_by(id=accessory_id).first()
        if not accessory:
            raise NotFoundError("EquipmentAccessory", accessory_id)

        if "name" in data:
            name = (data.get("name") or "").strip()
            if not name:
                raise ValidationError("اسم الملحق مطلوب.")
            accessory.name = name

        if "model_number" in data:
            accessory.model_number = data.get("model_number")
        if "serial_number" in data:
            accessory.serial_number = data.get("serial_number")
        if "manufacturer" in data:
            accessory.manufacturer = data.get("manufacturer")
        if "notes" in data:
            accessory.notes = data.get("notes")
        if "added_date" in data and data.get("added_date"):
            accessory.added_date = data.get("added_date")

        quantity = float(data.get("quantity", accessory.quantity) or 1.0)
        unit_cost = float(data.get("unit_cost", accessory.unit_cost) or 0.0)
        if quantity <= 0:
            raise ValidationError("الكمية يجب أن تكون أكبر من الصفر.")
        if unit_cost < 0:
            raise ValidationError("تكلفة الوحدة لا يمكن أن تكون سالبة.")

        accessory.quantity = quantity
        accessory.unit_cost = unit_cost
        accessory.total_cost = round(quantity * unit_cost, 2)

        db.commit()
        db.refresh(accessory)

        audit_service.log_action(
            db=db,
            user=user,
            action="UPDATE_ACCESSORY",
            entity_name="EquipmentAccessory",
            entity_id=str(accessory.id),
            details=f"تعديل ملحق '{accessory.name}' للجهاز رقم {accessory.equipment_id}"
        )
        return accessory

    def delete_accessory(self, db: Session, user, accessory_id: int) -> bool:
        check_permission(user, PERM_ACCESSORIES_MANAGE)
        accessory = db.query(EquipmentAccessory).filter_by(id=accessory_id).first()
        if not accessory:
            raise NotFoundError("EquipmentAccessory", accessory_id)

        name = accessory.name
        eq_id = accessory.equipment_id
        db.delete(accessory)
        db.commit()

        audit_service.log_action(
            db=db,
            user=user,
            action="DELETE_ACCESSORY",
            entity_name="EquipmentAccessory",
            entity_id=str(accessory_id),
            details=f"حذف ملحق '{name}' من الجهاز رقم {eq_id}"
        )
        return True

    def get_accessories(self, db: Session, equipment_id: int) -> List[EquipmentAccessory]:
        return db.query(EquipmentAccessory).filter_by(equipment_id=equipment_id).order_by(EquipmentAccessory.id.asc()).all()

    # ── Receiving & Commissioning Management ──────────────────────────────────
    def set_receiving_data(self, db: Session, user, equipment_id: int, data: Dict[str, Any]) -> EquipmentReceiving:
        check_permission(user, PERM_RECEIVING_MANAGE)
        eq = self.get_equipment_by_id(db, equipment_id)

        rec = db.query(EquipmentReceiving).filter_by(equipment_id=eq.id).first()
        if not rec:
            rec = EquipmentReceiving(
                equipment_id=eq.id,
                created_by_user_id=user.id if user else None
            )
            db.add(rec)

        rec.commissioning_number = data.get("commissioning_number")
        rec.commissioning_date = data.get("commissioning_date")
        rec.receipt_date = data.get("receipt_date")
        rec.receiving_technician_id = data.get("receiving_technician_id")
        rec.receiving_technician_name = data.get("receiving_technician_name")
        rec.registration_officer_id = data.get("registration_officer_id")
        rec.registration_officer_name = data.get("registration_officer_name")
        rec.registration_date = data.get("registration_date") or date.today()
        rec.receipt_report_number = data.get("receipt_report_number")
        rec.receipt_notes = data.get("receipt_notes")

        db.commit()
        db.refresh(rec)

        audit_service.log_action(
            db=db,
            user=user,
            action="SET_RECEIVING_DATA",
            entity_name="Equipment",
            entity_id=str(eq.id),
            details=f"تحديث بيانات الاستلام والتعميد للجهاز '{eq.name_ar}' (رقم التعميد: {rec.commissioning_number or '—'})"
        )
        return rec

    def get_receiving_data(self, db: Session, equipment_id: int) -> Optional[EquipmentReceiving]:
        return db.query(EquipmentReceiving).filter_by(equipment_id=equipment_id).first()

    list_equipment = get_equipment_list
    get_equipment_statistics = get_equipment_stats
    get_dashboard_statistics = get_equipment_stats


equipment_service = EquipmentService()
