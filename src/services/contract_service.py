"""
Contract & Warranty Service.
Manages maintenance service level agreements, warranties, and supplier agreements.
"""
from typing import List, Optional, Dict, Any
from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from src.models.contract import Contract
from src.models.vendor import Vendor
from src.services.audit_service import audit_service
from src.core.exceptions import ResourceNotFoundError, ValidationError


class ContractService:
    @staticmethod
    def create_contract(
        db: Session,
        vendor_id: int,
        contract_number: str,
        title: str,
        start_date: date,
        end_date: date,
        contract_type: str = "maintenance",
        cost: float = 0.0,
        terms: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> Contract:
        """Create a new service agreement or warranty."""
        if not contract_number or not contract_number.strip():
            raise ValidationError("Contract number is required")
        if not title or not title.strip():
            raise ValidationError("Contract title is required")
        if end_date < start_date:
            raise ValidationError("End date cannot be prior to start date")

        vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
        if not vendor:
            raise ValidationError(f"Vendor with ID {vendor_id} does not exist")

        existing = db.query(Contract).filter(Contract.contract_number == contract_number.strip()).first()
        if existing:
            raise ValidationError(f"Contract number '{contract_number}' already exists")

        contract = Contract(
            vendor_id=vendor_id,
            contract_number=contract_number.strip(),
            title=title.strip(),
            contract_type=contract_type,
            start_date=start_date,
            end_date=end_date,
            cost=max(0.0, float(cost)),
            terms=terms,
            is_active=True
        )
        db.add(contract)
        db.commit()
        db.refresh(contract)

        audit_service.log(
            db,
            action="CREATE",
            entity_type="Contract",
            entity_id=contract.id,
            user_id=user_id,
            details=f"Created Contract '{contract.contract_number}' ({contract.title})"
        )
        return contract

    @staticmethod
    def update_contract(
        db: Session,
        contract_id: int,
        user_id: Optional[int] = None,
        **kwargs
    ) -> Contract:
        """Update contract details."""
        contract = db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            raise ResourceNotFoundError(f"Contract with ID {contract_id} not found")

        for k, v in kwargs.items():
            if hasattr(contract, k) and v is not None:
                setattr(contract, k, v)

        db.commit()
        db.refresh(contract)

        audit_service.log(
            db,
            action="UPDATE",
            entity_type="Contract",
            entity_id=contract.id,
            user_id=user_id,
            details=f"Updated Contract '{contract.contract_number}'"
        )
        return contract

    @staticmethod
    def delete_contract(db: Session, contract_id: int, user_id: Optional[int] = None) -> bool:
        """Delete contract."""
        contract = db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            raise ResourceNotFoundError(f"Contract with ID {contract_id} not found")

        num = contract.contract_number
        db.delete(contract)
        db.commit()

        audit_service.log(
            db,
            action="DELETE",
            entity_type="Contract",
            entity_id=contract_id,
            user_id=user_id,
            details=f"Deleted Contract '{num}'"
        )
        return True

    @staticmethod
    def list_contracts(
        db: Session,
        contract_type: Optional[str] = None,
        vendor_id: Optional[int] = None,
        active_only: bool = False
    ) -> List[Contract]:
        """List contracts with filtering."""
        query = db.query(Contract)
        if active_only:
            query = query.filter(Contract.is_active.is_(True), Contract.end_date >= date.today())
        if contract_type and contract_type != "all":
            query = query.filter(Contract.contract_type == contract_type)
        if vendor_id:
            query = query.filter(Contract.vendor_id == vendor_id)

        return query.order_by(Contract.end_date.asc()).all()

    @staticmethod
    def get_contract_statistics(db: Session) -> Dict[str, Any]:
        """Get contract summary metrics."""
        today = date.today()
        soon = today + timedelta(days=30)

        total = db.query(func.count(Contract.id)).scalar() or 0
        active = db.query(func.count(Contract.id)).filter(Contract.is_active.is_(True), Contract.end_date >= today).scalar() or 0
        expiring_soon = db.query(func.count(Contract.id)).filter(
            Contract.is_active.is_(True),
            Contract.end_date >= today,
            Contract.end_date <= soon
        ).scalar() or 0
        total_val = db.query(func.sum(Contract.cost)).filter(Contract.is_active.is_(True)).scalar() or 0.0

        return {
            "total": total,
            "active": active,
            "expiring_soon": expiring_soon,
            "total_value": round(float(total_val), 2)
        }


contract_service = ContractService()
