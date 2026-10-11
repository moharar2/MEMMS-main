"""
Preventive Maintenance (PM) Plans, Schedules, and Execution records.
"""
from sqlalchemy import Column, String, Integer, Float, Date, DateTime, Text, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from src.models.base import BaseModel, utc_now


class PMPlan(BaseModel):
    __tablename__ = "pm_plans"

    equipment_id = Column(Integer, ForeignKey("equipment.id", ondelete="CASCADE"), nullable=True)
    category = Column(String(100), nullable=True)  # Can be applied to individual equipment or all in a category
    title = Column(String(150), nullable=False)
    frequency_days = Column(Integer, nullable=False, default=90)  # e.g., 30 (monthly), 90 (quarterly), 180 (biannual), 365 (annual)
    checklist_template = Column(JSON, default=list, nullable=False)  # List of checklist items
    estimated_duration_minutes = Column(Integer, default=60, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    equipment = relationship("Equipment", back_populates="pm_plans")
    schedules = relationship("PMSchedule", back_populates="plan", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<PMPlan(title='{self.title}', freq={self.frequency_days}d)>"


class PMSchedule(BaseModel):
    __tablename__ = "pm_schedules"

    pm_plan_id = Column(Integer, ForeignKey("pm_plans.id", ondelete="CASCADE"), nullable=False)
    equipment_id = Column(Integer, ForeignKey("equipment.id", ondelete="CASCADE"), nullable=False)
    due_date = Column(Date, nullable=False, index=True)
    status = Column(String(30), default="scheduled", nullable=False, index=True)  # 'scheduled', 'overdue', 'completed', 'cancelled'

    plan = relationship("PMPlan", back_populates="schedules")
    equipment = relationship("Equipment", back_populates="pm_schedules")
    execution = relationship("PMExecution", back_populates="schedule", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<PMSchedule(equipment_id={self.equipment_id}, due_date={self.due_date}, status='{self.status}')>"


class PMExecution(BaseModel):
    __tablename__ = "pm_executions"

    pm_schedule_id = Column(Integer, ForeignKey("pm_schedules.id", ondelete="CASCADE"), nullable=False, unique=True)
    equipment_id = Column(Integer, ForeignKey("equipment.id", ondelete="CASCADE"), nullable=False)
    technician_id = Column(Integer, ForeignKey("technicians.id", ondelete="RESTRICT"), nullable=False)

    execution_date = Column(DateTime, default=utc_now, nullable=False)
    completion_date = Column(DateTime, nullable=True)

    passed = Column(Boolean, default=True, nullable=False)
    results_summary = Column(Text, nullable=True)
    measurements = Column(JSON, default=dict, nullable=False)  # Measurement values recorded during calibration/safety checks
    notes = Column(Text, nullable=True)
    next_due_date = Column(Date, nullable=True)

    schedule = relationship("PMSchedule", back_populates="execution")
    equipment = relationship("Equipment", back_populates="pm_executions")
    technician = relationship("Technician", back_populates="pm_executions")

    def __repr__(self):
        return f"<PMExecution(equipment_id={self.equipment_id}, passed={self.passed}, date={self.execution_date})>"
