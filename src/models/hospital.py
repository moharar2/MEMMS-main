"""
Hospital, Department, and Room/Location hierarchy models.
"""
from sqlalchemy import Column, String, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from src.models.base import BaseModel


class Hospital(BaseModel):
    __tablename__ = "hospitals"

    name_ar = Column(String(150), nullable=False)
    name_en = Column(String(150), nullable=False)
    code = Column(String(50), unique=True, nullable=False, index=True)
    address = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    departments = relationship("Department", back_populates="hospital", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Hospital(name='{self.name_ar}', code='{self.code}')>"


class Department(BaseModel):
    __tablename__ = "departments"

    hospital_id = Column(Integer, ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False)
    name_ar = Column(String(150), nullable=False)
    name_en = Column(String(150), nullable=False)
    code = Column(String(50), nullable=False, index=True)
    floor = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    hospital = relationship("Hospital", back_populates="departments")
    locations = relationship("Location", back_populates="department", cascade="all, delete-orphan")
    equipment = relationship("Equipment", back_populates="department")
    work_orders = relationship("WorkOrder", back_populates="department")

    def __repr__(self):
        return f"<Department(name='{self.name_ar}', code='{self.code}')>"


class Location(BaseModel):
    __tablename__ = "locations"

    department_id = Column(Integer, ForeignKey("departments.id", ondelete="CASCADE"), nullable=False)
    room_number = Column(String(50), nullable=False, index=True)
    room_name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)

    department = relationship("Department", back_populates="locations")
    equipment = relationship("Equipment", back_populates="location")

    def __repr__(self):
        return f"<Location(room_number='{self.room_number}', name='{self.room_name}')>"
