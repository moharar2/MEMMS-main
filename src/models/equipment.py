"""
Medical Equipment entity model, equipment transfer history, accessories, and receiving/commissioning data.
"""
from datetime import date
from sqlalchemy import Column, String, Integer, Float, Date, Text, ForeignKey
from sqlalchemy.orm import relationship
from src.models.base import BaseModel


class Equipment(BaseModel):
    __tablename__ = "equipment"

    asset_number = Column(String(50), unique=True, nullable=False, index=True)
    inventory_number = Column(String(50), nullable=True, index=True)
    serial_number = Column(String(100), unique=True, nullable=False, index=True)

    name_ar = Column(String(150), nullable=False, index=True)
    name_en = Column(String(150), nullable=False, index=True)
    model = Column(String(100), nullable=True)
    category = Column(String(100), nullable=False, index=True)  # e.g., 'Ventilator', 'Monitor', 'Infusion Pump', 'Defibrillator'

    # Vendors relationships
    manufacturer_id = Column(Integer, ForeignKey("vendors.id", ondelete="SET NULL"), nullable=True)
    supplier_id = Column(Integer, ForeignKey("vendors.id", ondelete="SET NULL"), nullable=True)
    agent_id = Column(Integer, ForeignKey("vendors.id", ondelete="SET NULL"), nullable=True)
    assigned_engineer_id = Column(Integer, ForeignKey("vendor_engineers.id", ondelete="SET NULL"), nullable=True)

    # Location relationships
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id", ondelete="SET NULL"), nullable=True)

    # Dates and Lifecycle
    purchase_date = Column(Date, nullable=True)
    installation_date = Column(Date, nullable=True)
    warranty_expiry_date = Column(Date, nullable=True)
    purchase_price = Column(Float, default=0.0, nullable=False)

    # Operational Status and Risk
    status = Column(String(50), default="operational", nullable=False, index=True)
    # Statuses: 'operational', 'under_maintenance', 'out_of_service', 'scrapped', 'standby'
    
    risk_level = Column(String(30), default="medium", nullable=False)  # 'high', 'medium', 'low'
    criticality = Column(String(30), default="semi_critical", nullable=False)  # 'critical', 'semi_critical', 'non_critical'
    notes = Column(Text, nullable=True)

    # Relationships
    department = relationship("Department", back_populates="equipment")
    location = relationship("Location", back_populates="equipment")
    manufacturer = relationship("Vendor", foreign_keys=[manufacturer_id], back_populates="manufactured_equipment")
    supplier = relationship("Vendor", foreign_keys=[supplier_id], back_populates="supplied_equipment")
    agent = relationship("Vendor", foreign_keys=[agent_id], back_populates="serviced_equipment")
    assigned_engineer = relationship("VendorEngineer", foreign_keys=[assigned_engineer_id])

    work_orders = relationship("WorkOrder", back_populates="equipment", cascade="all, delete-orphan")
    pm_plans = relationship("PMPlan", back_populates="equipment", cascade="all, delete-orphan")
    pm_schedules = relationship("PMSchedule", back_populates="equipment", cascade="all, delete-orphan")
    pm_executions = relationship("PMExecution", back_populates="equipment", cascade="all, delete-orphan")
    transfers = relationship("EquipmentTransfer", back_populates="equipment", cascade="all, delete-orphan")

    accessories = relationship("EquipmentAccessory", back_populates="equipment", cascade="all, delete-orphan")
    receiving = relationship("EquipmentReceiving", back_populates="equipment", uselist=False, cascade="all, delete-orphan")

    @property
    def total_accessories_cost(self) -> float:
        return sum(float(a.total_cost or 0.0) for a in (self.accessories or []))

    @property
    def total_asset_cost(self) -> float:
        return float(self.purchase_price or 0.0) + self.total_accessories_cost

    def __repr__(self):
        return f"<Equipment(asset='{self.asset_number}', name='{self.name_ar}', status='{self.status}')>"


class EquipmentAccessory(BaseModel):
    __tablename__ = "equipment_accessories"

    equipment_id = Column(Integer, ForeignKey("equipment.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    model_number = Column(String(100), nullable=True)
    serial_number = Column(String(100), nullable=True)
    manufacturer = Column(String(150), nullable=True)
    quantity = Column(Float, default=1.0, nullable=False)
    unit_cost = Column(Float, default=0.0, nullable=False)
    total_cost = Column(Float, default=0.0, nullable=False)
    added_date = Column(Date, default=date.today, nullable=False)
    notes = Column(Text, nullable=True)

    equipment = relationship("Equipment", back_populates="accessories")

    def __repr__(self):
        return f"<EquipmentAccessory(name='{self.name}', qty={self.quantity}, total={self.total_cost})>"


class EquipmentReceiving(BaseModel):
    __tablename__ = "equipment_receivings"

    equipment_id = Column(Integer, ForeignKey("equipment.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    commissioning_number = Column(String(100), nullable=True)  # رقم التعميد
    commissioning_date = Column(Date, nullable=True)  # تاريخ التعميد
    receipt_date = Column(Date, nullable=True)  # تاريخ استلام الجهاز
    receiving_technician_id = Column(Integer, ForeignKey("technicians.id", ondelete="SET NULL"), nullable=True)  # فني الاستلام
    receiving_technician_name = Column(String(150), nullable=True)
    registration_officer_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)  # مسؤول تسجيل الجهاز
    registration_officer_name = Column(String(150), nullable=True)
    registration_date = Column(Date, default=date.today, nullable=True)  # تاريخ تسجيل الجهاز
    receipt_report_number = Column(String(100), nullable=True)  # رقم محضر الاستلام
    receipt_notes = Column(Text, nullable=True)  # ملاحظات الاستلام
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    equipment = relationship("Equipment", back_populates="receiving")
    receiving_technician = relationship("Technician", foreign_keys=[receiving_technician_id])
    registration_officer = relationship("User", foreign_keys=[registration_officer_id])
    created_by = relationship("User", foreign_keys=[created_by_user_id])

    def __repr__(self):
        return f"<EquipmentReceiving(equipment_id={self.equipment_id}, comm_no='{self.commissioning_number}')>"


class EquipmentTransfer(BaseModel):
    __tablename__ = "equipment_transfers"

    equipment_id = Column(Integer, ForeignKey("equipment.id", ondelete="CASCADE"), nullable=False)
    from_department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    to_department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    from_location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    to_location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    transfer_date = Column(Date, nullable=False)
    reason = Column(Text, nullable=True)
    transferred_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    equipment = relationship("Equipment", back_populates="transfers")
    from_department = relationship("Department", foreign_keys=[from_department_id])
    to_department = relationship("Department", foreign_keys=[to_department_id])
    from_location = relationship("Location", foreign_keys=[from_location_id])
    to_location = relationship("Location", foreign_keys=[to_location_id])
    transferred_by = relationship("User", foreign_keys=[transferred_by_user_id])

    def __repr__(self):
        return f"<EquipmentTransfer(equipment_id={self.equipment_id}, date={self.transfer_date})>"
