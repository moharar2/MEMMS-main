"""
models.py
---------
SQLAlchemy 2.x declarative models for MEMMS.

These are the *foundational* tables for Phase 1. CRUD screens, validation,
and business logic come in later phases — so we keep relationships and
constraints correct, but we do not add heavy logic here.

Conventions used throughout:
- Integer primary keys (simple, easy to read for beginners).
- `name_ar` / `name_en` pairs for entities displayed bilingually.
- Money columns use `Numeric(12, 2)` and map to Python `Decimal` — never
  store money in floats.
- Status enums are plain strings here (with a comment listing allowed
  values). We will tighten these into Python enums in Phase 2 if needed.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,    Float,    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


# ---------------------------------------------------------------------------
# Department — a hospital department that owns equipment.
# ---------------------------------------------------------------------------
class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name_ar: Mapped[str] = mapped_column(String(120), nullable=False)
    name_en: Mapped[str] = mapped_column(String(120), nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(120))

    # Relationships: one department has many staff and many equipment.
    staff: Mapped[List["Staff"]] = relationship(back_populates="department")
    equipment: Mapped[List["Equipment"]] = relationship(back_populates="department")

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"<Department {self.id} {self.name_en}>"


# ---------------------------------------------------------------------------
# Staff — hospital employees and technicians who maintain equipment.
# ---------------------------------------------------------------------------
class Staff(Base):
    __tablename__ = "staff"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # `staff_code` is the unique employee ID / badge number.
    staff_code: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(160), nullable=False)
    position: Mapped[Optional[str]] = mapped_column(String(120))  # Job title / role
    specialization: Mapped[Optional[str]] = mapped_column(String(120))  # e.g., Biomedical, Radiology, Electronics
    department_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("departments.id"), nullable=True
    )
    phone: Mapped[Optional[str]] = mapped_column(String(40))
    email: Mapped[Optional[str]] = mapped_column(String(120))
    hire_date: Mapped[Optional[date]] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Legacy / supplemental fields
    nationality: Mapped[Optional[str]] = mapped_column(String(60))
    qualification: Mapped[Optional[str]] = mapped_column(String(160))
    experience: Mapped[Optional[str]] = mapped_column(String(120))

    department: Mapped[Optional["Department"]] = relationship(back_populates="staff")
    equipment: Mapped[List["Equipment"]] = relationship(back_populates="assigned_staff")
    work_orders: Mapped[List["WorkOrder"]] = relationship(back_populates="assigned_staff")

    # Property aliases for Phase 3 UI conventions
    @property
    def staff_id(self) -> str:
        return self.staff_code

    @staff_id.setter
    def staff_id(self, val: str) -> None:
        self.staff_code = val

    @property
    def job_title(self) -> Optional[str]:
        return self.position

    @job_title.setter
    def job_title(self, val: Optional[str]) -> None:
        self.position = val

    @property
    def specialty(self) -> Optional[str]:
        return self.specialization

    @specialty.setter
    def specialty(self, val: Optional[str]) -> None:
        self.specialization = val

    @property
    def status(self) -> str:
        return "active" if self.is_active else "inactive"

    @status.setter
    def status(self, val: str) -> None:
        self.is_active = (val == "active" or val is True)

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"<Staff {self.id} [{self.staff_code}] {self.full_name}>"


# ---------------------------------------------------------------------------
# Equipment — medical devices tracked by the hospital.
# ---------------------------------------------------------------------------
class Equipment(Base):
    __tablename__ = "equipment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # `hospital_code` is the internal asset code printed on the label.
    # It must be unique across the hospital.
    hospital_code: Mapped[str] = mapped_column(String(60), nullable=False, unique=True)

    name_ar: Mapped[str] = mapped_column(String(160), nullable=False)
    name_en: Mapped[str] = mapped_column(String(160), nullable=False)
    model: Mapped[Optional[str]] = mapped_column(String(120))
    manufacturer: Mapped[Optional[str]] = mapped_column(String(120))
    official_agent: Mapped[Optional[str]] = mapped_column(String(120))
    serial_number: Mapped[Optional[str]] = mapped_column(String(120))
    classification: Mapped[Optional[str]] = mapped_column(String(120))
    equipment_type: Mapped[Optional[str]] = mapped_column(String(120))

    # Money: use Numeric + Decimal. Phase 2 CRUD screens will keep Decimal.
    purchase_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    useful_life_years: Mapped[Optional[int]] = mapped_column(Integer)

    commissioning_number: Mapped[Optional[str]] = mapped_column(String(60))
    commissioning_date: Mapped[Optional[date]] = mapped_column(Date)
    received_date: Mapped[Optional[date]] = mapped_column(Date)
    warranty_end: Mapped[Optional[date]] = mapped_column(Date)

    department_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("departments.id"), nullable=True
    )
    assigned_staff_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("staff.id"), nullable=True
    )

    # Allowed values (Phase 1 hint, not enforced):
    #   "operational", "under_maintenance", "out_of_service", "retired"
    status: Mapped[Optional[str]] = mapped_column(String(40))

    notes: Mapped[Optional[str]] = mapped_column(Text)

    department: Mapped[Optional["Department"]] = relationship(back_populates="equipment")
    assigned_staff: Mapped[Optional["Staff"]] = relationship(back_populates="equipment")

    work_orders: Mapped[List["WorkOrder"]] = relationship(back_populates="equipment")
    maintenance_plans: Mapped[List["MaintenancePlan"]] = relationship(
        back_populates="equipment"
    )


# ---------------------------------------------------------------------------
# WorkOrder — corrective or preventive maintenance job on one piece of
# equipment.
# ---------------------------------------------------------------------------
class WorkOrder(Base):
    __tablename__ = "work_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # `order_number` is shown to staff; it must be unique.
    order_number: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)

    equipment_id: Mapped[int] = mapped_column(
        ForeignKey("equipment.id"), nullable=False
    )
    assigned_staff_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("staff.id"), nullable=True
    )

    # Allowed values:
    #   maintenance_type: "corrective", "preventive", "calibration", "inspection"
    #   status:           "open", "in_progress", "closed", "cancelled"
    maintenance_type: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="open")

    problem_description: Mapped[Optional[str]] = mapped_column(Text)
    diagnosis: Mapped[Optional[str]] = mapped_column(Text)
    repair_actions: Mapped[Optional[str]] = mapped_column(Text)

    opened_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    equipment: Mapped["Equipment"] = relationship(back_populates="work_orders")
    assigned_staff: Mapped[Optional["Staff"]] = relationship(back_populates="work_orders")
    parts_used: Mapped[List["WorkOrderPart"]] = relationship(back_populates="work_order")


# ---------------------------------------------------------------------------
# SparePart — inventory item that can be consumed by work orders.
# ---------------------------------------------------------------------------
class SparePart(Base):
    __tablename__ = "spare_parts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    part_number: Mapped[str] = mapped_column(String(60), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)

    unit_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0"))
    quantity_in_stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    used_in: Mapped[List["WorkOrderPart"]] = relationship(back_populates="spare_part")


# ---------------------------------------------------------------------------
# WorkOrderPart — join table: which parts went into which work order, and
# how many, plus the cost snapshot at the moment of use.
# ---------------------------------------------------------------------------
class WorkOrderPart(Base):
    __tablename__ = "work_order_parts"
    __table_args__ = (
        UniqueConstraint("work_order_id", "spare_part_id", name="uq_work_order_part"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    work_order_id: Mapped[int] = mapped_column(
        ForeignKey("work_orders.id"), nullable=False
    )
    spare_part_id: Mapped[int] = mapped_column(
        ForeignKey("spare_parts.id"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    unit_cost_at_use: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0")
    )

    work_order: Mapped["WorkOrder"] = relationship(back_populates="parts_used")
    spare_part: Mapped["SparePart"] = relationship(back_populates="used_in")


# ---------------------------------------------------------------------------
# MaintenancePlan — preventive maintenance schedule for one piece of
# equipment.
# ---------------------------------------------------------------------------
class MaintenancePlan(Base):
    __tablename__ = "maintenance_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    equipment_id: Mapped[int] = mapped_column(
        ForeignKey("equipment.id"), nullable=False
    )
    interval_days: Mapped[int] = mapped_column(Integer, nullable=False)
    next_due_date: Mapped[Optional[date]] = mapped_column(Date)
    checklist: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    equipment: Mapped["Equipment"] = relationship(back_populates="maintenance_plans")
