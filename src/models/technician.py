"""
Technician, biomedical engineer profile, qualifications, experiences, and compensation models.
"""
from datetime import date
from sqlalchemy import Column, String, Integer, Float, Date, Text, ForeignKey
from sqlalchemy.orm import relationship
from src.models.base import BaseModel


class Technician(BaseModel):
    __tablename__ = "technicians"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, unique=True)
    employee_id = Column(String(50), unique=True, nullable=False, index=True)
    full_name = Column(String(100), nullable=False, index=True)
    specialization = Column(String(100), nullable=False)  # e.g., 'Radiology', 'ICU & Anesthesia', 'Laboratory', 'General'
    phone = Column(String(50), nullable=True)
    email = Column(String(120), nullable=True)
    qualification = Column(String(150), nullable=True)  # Primary qualification summary
    status = Column(String(30), default="active", nullable=False)  # 'active', 'on_leave', 'inactive'

    # Extended Personal & Administrative Data
    nationality = Column(String(50), nullable=True)
    id_document_type = Column(String(50), default="national_id", nullable=True)  # 'national_id', 'iqama', 'passport'
    id_number = Column(String(50), nullable=True, index=True)
    job_title = Column(String(100), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    work_entity = Column(String(150), nullable=True)  # e.g., 'مستشفى الملك فهد', 'الشركة المشغلة'
    hire_date = Column(Date, nullable=True)

    # Relationships
    user = relationship("User", back_populates="technician_profile")
    department = relationship("Department")
    work_orders = relationship("WorkOrder", back_populates="assigned_technician")
    pm_executions = relationship("PMExecution", back_populates="technician")

    qualifications = relationship("TechnicianQualification", back_populates="technician", cascade="all, delete-orphan")
    experiences = relationship("TechnicianExperience", back_populates="technician", cascade="all, delete-orphan")
    compensations = relationship("TechnicianCompensation", back_populates="technician", cascade="all, delete-orphan")

    @property
    def id_number_masked(self) -> str:
        """Masks national ID/iqama for privacy in general views (e.g. ******1234)."""
        if not self.id_number or len(self.id_number.strip()) < 4:
            return "—"
        clean = self.id_number.strip()
        return ("*" * (len(clean) - 4)) + clean[-4:]

    def __repr__(self):
        return f"<Technician(name='{self.full_name}', emp_id='{self.employee_id}', status='{self.status}')>"


class TechnicianQualification(BaseModel):
    __tablename__ = "technician_qualifications"

    technician_id = Column(Integer, ForeignKey("technicians.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(150), nullable=False)  # اسم المؤهل أو الشهادة
    specialization = Column(String(100), nullable=True)  # التخصص
    issuing_organization = Column(String(150), nullable=True)  # الجهة المانحة
    issue_date = Column(Date, nullable=True)  # تاريخ الحصول عليها
    expiry_date = Column(Date, nullable=True)  # تاريخ الانتهاء إن وجد
    notes = Column(Text, nullable=True)
    attachment_path = Column(String(500), nullable=True)  # نسخة إلكترونية من الشهادة

    technician = relationship("Technician", back_populates="qualifications")

    def __repr__(self):
        return f"<TechnicianQualification(name='{self.name}', tech_id={self.technician_id})>"


class TechnicianExperience(BaseModel):
    __tablename__ = "technician_experiences"

    technician_id = Column(Integer, ForeignKey("technicians.id", ondelete="CASCADE"), nullable=False, index=True)
    previous_employer = Column(String(150), nullable=False)  # جهة العمل السابقة
    job_title = Column(String(100), nullable=False)  # المسمى الوظيفي
    specialization = Column(String(100), nullable=True)  # التخصص
    start_date = Column(Date, nullable=False)  # تاريخ البداية
    end_date = Column(Date, nullable=True)  # تاريخ النهاية
    task_description = Column(Text, nullable=True)  # وصف المهام

    technician = relationship("Technician", back_populates="experiences")

    @property
    def calculated_years(self) -> float:
        """Calculates years of experience from start_date to end_date or today."""
        if not self.start_date:
            return 0.0
        finish = self.end_date or date.today()
        days = (finish - self.start_date).days
        return round(max(0.0, days / 365.25), 1)

    def __repr__(self):
        return f"<TechnicianExperience(employer='{self.previous_employer}', title='{self.job_title}')>"


class TechnicianCompensation(BaseModel):
    __tablename__ = "technician_compensations"

    technician_id = Column(Integer, ForeignKey("technicians.id", ondelete="CASCADE"), nullable=False, index=True)
    basic_salary = Column(Float, default=0.0, nullable=False)
    allowances = Column(Float, default=0.0, nullable=False)
    allowance_type = Column(String(100), nullable=True)  # 'بدل سكن ونقل', 'بدل طبيعة عمل', etc.
    total_package = Column(Float, default=0.0, nullable=False)
    effective_date = Column(Date, default=date.today, nullable=False)
    notes = Column(Text, nullable=True)

    technician = relationship("Technician", back_populates="compensations")

    def __repr__(self):
        return f"<TechnicianCompensation(tech_id={self.technician_id}, total={self.total_package})>"
