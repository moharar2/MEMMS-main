"""
Corrective Work Orders, Status transition logs, and Spare parts consumed per order.
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from src.models.base import BaseModel, utc_now


class WorkOrder(BaseModel):
    __tablename__ = "work_orders"

    work_order_number = Column(String(50), unique=True, nullable=False, index=True)
    equipment_id = Column(Integer, ForeignKey("equipment.id", ondelete="RESTRICT"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False)

    reported_by_name = Column(String(100), nullable=False)
    reporter_contact = Column(String(50), nullable=True)
    report_date = Column(DateTime, default=utc_now, nullable=False)

    priority = Column(String(30), default="medium", nullable=False)  # 'critical', 'high', 'medium', 'low'
    failure_description = Column(Text, nullable=False)
    symptoms = Column(Text, nullable=True)

    assigned_technician_id = Column(Integer, ForeignKey("technicians.id", ondelete="SET NULL"), nullable=True)

    diagnosis = Column(Text, nullable=True)
    corrective_action = Column(Text, nullable=True)
    failure_cause = Column(Text, nullable=True)

    status = Column(String(50), default="pending", nullable=False, index=True)
    # 'pending', 'assigned', 'in_progress', 'waiting_parts', 'completed', 'closed', 'cancelled'

    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    closed_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    total_labor_cost = Column(Float, default=0.0, nullable=False)
    total_parts_cost = Column(Float, default=0.0, nullable=False)

    # Relationships
    equipment = relationship("Equipment", back_populates="work_orders")
    department = relationship("Department", back_populates="work_orders")
    assigned_technician = relationship("Technician", back_populates="work_orders")
    closed_by_user = relationship("User", foreign_keys=[closed_by_user_id])
    
    status_logs = relationship("WorkOrderLog", back_populates="work_order", cascade="all, delete-orphan", order_by="WorkOrderLog.timestamp.desc()")
    consumed_parts = relationship("WorkOrderPart", back_populates="work_order", cascade="all, delete-orphan")

    @property
    def total_cost(self) -> float:
        return float(self.total_labor_cost or 0.0) + float(self.total_parts_cost or 0.0)

    def __repr__(self):
        return f"<WorkOrder(number='{self.work_order_number}', status='{self.status}', priority='{self.priority}')>"


class WorkOrderLog(BaseModel):
    __tablename__ = "work_order_logs"

    work_order_id = Column(Integer, ForeignKey("work_orders.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    from_status = Column(String(50), nullable=True)
    to_status = Column(String(50), nullable=False)
    notes = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=utc_now, nullable=False)

    work_order = relationship("WorkOrder", back_populates="status_logs")
    user = relationship("User")

    def __repr__(self):
        return f"<WorkOrderLog(wo_id={self.work_order_id}, to_status='{self.to_status}')>"


class WorkOrderPart(BaseModel):
    __tablename__ = "work_order_parts"

    work_order_id = Column(Integer, ForeignKey("work_orders.id", ondelete="CASCADE"), nullable=False)
    part_id = Column(Integer, ForeignKey("spare_parts.id", ondelete="RESTRICT"), nullable=False)
    quantity = Column(Float, nullable=False, default=1.0)
    unit_price = Column(Float, nullable=False, default=0.0)
    total_price = Column(Float, nullable=False, default=0.0)

    work_order = relationship("WorkOrder", back_populates="consumed_parts")
    part = relationship("SparePart")

    def __repr__(self):
        return f"<WorkOrderPart(wo_id={self.work_order_id}, part_id={self.part_id}, qty={self.quantity})>"
