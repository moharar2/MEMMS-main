"""
Biomedical Spare Parts and Inventory Management Service.
Manages spare parts catalog, stock levels, reorder thresholds, and transactions.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from src.models.inventory import SparePart, InventoryTransaction
from src.models.vendor import Vendor
from src.services.audit_service import audit_service
from src.core.exceptions import ResourceNotFoundError, ValidationError


class InventoryService:
    @staticmethod
    def create_spare_part(
        db: Session,
        part_number: str,
        name_ar: str,
        name_en: str,
        category: str,
        storage_bin_location: Optional[str] = None,
        quantity_on_hand: float = 0.0,
        minimum_reorder_level: float = 5.0,
        unit_cost: float = 0.0,
        unit_of_measure: str = "Piece",
        manufacturer_id: Optional[int] = None,
        description: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> SparePart:
        """Create a new spare part entry."""
        if not part_number or not part_number.strip():
            raise ValidationError("Part Number / SKU is required")
        if not name_en and not name_ar:
            raise ValidationError("Part name is required")

        existing = db.query(SparePart).filter(SparePart.part_number == part_number.strip()).first()
        if existing:
            raise ValidationError(f"Part Number '{part_number}' already exists")

        if manufacturer_id:
            vendor = db.query(Vendor).filter(Vendor.id == manufacturer_id).first()
            if not vendor:
                raise ValidationError("Manufacturer / Vendor not found")

        part = SparePart(
            part_number=part_number.strip().upper(),
            name_ar=name_ar.strip() if name_ar else name_en.strip(),
            name_en=name_en.strip() if name_en else name_ar.strip(),
            category=category.strip(),
            storage_bin_location=storage_bin_location.strip() if storage_bin_location else None,
            quantity_on_hand=max(0.0, float(quantity_on_hand)),
            minimum_reorder_level=max(0.0, float(minimum_reorder_level)),
            unit_cost=max(0.0, float(unit_cost)),
            unit_of_measure=unit_of_measure or "Piece",
            manufacturer_id=manufacturer_id,
            description=description,
            is_active=True
        )
        db.add(part)
        db.commit()
        db.refresh(part)

        audit_service.log(
            db,
            action="CREATE",
            entity_type="SparePart",
            entity_id=part.id,
            user_id=user_id,
            details=f"Created Spare Part '{part.part_number}' ({part.name_en})"
        )
        return part

    @staticmethod
    def update_spare_part(
        db: Session,
        part_id: int,
        user_id: Optional[int] = None,
        **kwargs
    ) -> SparePart:
        """Update spare part catalog information."""
        part = db.query(SparePart).filter(SparePart.id == part_id).first()
        if not part:
            raise ResourceNotFoundError(f"Spare part with ID {part_id} not found")

        if "part_number" in kwargs and kwargs["part_number"]:
            new_no = kwargs["part_number"].strip().upper()
            if new_no != part.part_number:
                exists = db.query(SparePart).filter(SparePart.part_number == new_no).first()
                if exists:
                    raise ValidationError(f"Part Number '{new_no}' already exists")
                part.part_number = new_no

        for k, v in kwargs.items():
            if k != "part_number" and hasattr(part, k) and v is not None:
                setattr(part, k, v)

        db.commit()
        db.refresh(part)

        audit_service.log(
            db,
            action="UPDATE",
            entity_type="SparePart",
            entity_id=part.id,
            user_id=user_id,
            details=f"Updated Spare Part '{part.part_number}'"
        )
        return part

    @staticmethod
    def delete_spare_part(db: Session, part_id: int, user_id: Optional[int] = None) -> bool:
        """Delete spare part."""
        part = db.query(SparePart).filter(SparePart.id == part_id).first()
        if not part:
            raise ResourceNotFoundError(f"Spare part with ID {part_id} not found")

        part_num = part.part_number
        db.delete(part)
        db.commit()

        audit_service.log(
            db,
            action="DELETE",
            entity_type="SparePart",
            entity_id=part_id,
            user_id=user_id,
            details=f"Deleted Spare Part '{part_num}'"
        )
        return True

    @staticmethod
    def record_transaction(
        db: Session,
        part_id: int,
        transaction_type: str,
        quantity: float,
        unit_cost: Optional[float] = None,
        work_order_id: Optional[int] = None,
        reference_number: Optional[str] = None,
        notes: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> InventoryTransaction:
        """Record stock in, stock out, or adjustment and update stock on hand."""
        part = db.query(SparePart).filter(SparePart.id == part_id).first()
        if not part:
            raise ResourceNotFoundError(f"Spare part with ID {part_id} not found")

        qty = float(quantity)
        cost = unit_cost if unit_cost is not None else part.unit_cost

        if transaction_type in ["in_purchase", "in_return"]:
            if qty <= 0:
                raise ValidationError("Quantity for stock-in must be greater than 0")
            part.quantity_on_hand += qty
            if unit_cost is not None and unit_cost > 0:
                part.unit_cost = unit_cost
        elif transaction_type == "out_work_order":
            if qty <= 0:
                raise ValidationError("Quantity for stock-out must be greater than 0")
            if part.quantity_on_hand < qty:
                raise ValidationError(f"Insufficient stock on hand ({part.quantity_on_hand} available)")
            part.quantity_on_hand -= qty
        elif transaction_type == "adjustment":
            if qty < 0:
                raise ValidationError("Adjusted stock balance cannot be negative")
            part.quantity_on_hand = qty
        else:
            raise ValidationError(f"Unknown transaction type: {transaction_type}")

        tx = InventoryTransaction(
            part_id=part.id,
            transaction_type=transaction_type,
            quantity=qty,
            unit_cost=cost,
            work_order_id=work_order_id,
            reference_number=reference_number,
            notes=notes,
            user_id=user_id
        )
        db.add(tx)
        db.commit()
        db.refresh(tx)

        audit_service.log(
            db,
            action="INVENTORY_TX",
            entity_type="InventoryTransaction",
            entity_id=tx.id,
            user_id=user_id,
            details=f"{transaction_type} {qty} {part.unit_of_measure} for part {part.part_number}"
        )
        return tx

    @staticmethod
    def list_spare_parts(
        db: Session,
        low_stock_only: bool = False,
        category: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[SparePart]:
        """List spare parts with filtering."""
        query = db.query(SparePart).filter(SparePart.is_active.is_(True))

        if low_stock_only:
            query = query.filter(SparePart.quantity_on_hand <= SparePart.minimum_reorder_level)
        if category and category != "all":
            query = query.filter(SparePart.category == category)
        if search:
            s = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    SparePart.part_number.ilike(s),
                    SparePart.name_en.ilike(s),
                    SparePart.name_ar.ilike(s),
                    SparePart.storage_bin_location.ilike(s)
                )
            )
        return query.order_by(SparePart.part_number.asc()).all()

    @staticmethod
    def get_inventory_statistics(db: Session) -> Dict[str, Any]:
        """Get inventory overview KPIs."""
        total_parts = db.query(func.count(SparePart.id)).filter(SparePart.is_active.is_(True)).scalar() or 0
        
        low_stock_count = db.query(func.count(SparePart.id)).filter(
            SparePart.is_active.is_(True),
            SparePart.quantity_on_hand <= SparePart.minimum_reorder_level
        ).scalar() or 0

        # Valuation
        parts = db.query(SparePart.quantity_on_hand, SparePart.unit_cost).filter(SparePart.is_active.is_(True)).all()
        total_value = sum(p[0] * p[1] for p in parts)

        return {
            "total_parts": total_parts,
            "low_stock_count": low_stock_count,
            "total_value": round(total_value, 2)
        }


inventory_service = InventoryService()
