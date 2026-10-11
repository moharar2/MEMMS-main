"""
Vendor model for manufacturers, suppliers, maintenance agents, and service providers.
"""
from sqlalchemy import Column, String, Text, Integer, ForeignKey
from sqlalchemy.orm import relationship
from src.models.base import BaseModel


class Vendor(BaseModel):
    __tablename__ = "vendors"

    name = Column(String(150), nullable=False, index=True)
    vendor_type = Column(String(50), nullable=False, default="supplier")  # 'manufacturer', 'supplier', 'agent', 'service_provider'
    contact_person = Column(String(100), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(120), nullable=True)
    address = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)

    contracts = relationship("Contract", back_populates="vendor", cascade="all, delete-orphan")
    supplied_equipment = relationship("Equipment", foreign_keys="Equipment.supplier_id", back_populates="supplier")
    manufactured_equipment = relationship("Equipment", foreign_keys="Equipment.manufacturer_id", back_populates="manufacturer")
    serviced_equipment = relationship("Equipment", foreign_keys="Equipment.agent_id", back_populates="agent")
    spare_parts = relationship("SparePart", back_populates="manufacturer")
    engineers = relationship("VendorEngineer", back_populates="vendor", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Vendor(name='{self.name}', type='{self.vendor_type}')>"


class VendorEngineer(BaseModel):
    __tablename__ = "vendor_engineers"

    vendor_id = Column(Integer, ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(120), nullable=False, index=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(120), nullable=True)
    specialization = Column(String(100), nullable=True)  # e.g., 'Biomedical Support', 'Imaging Systems', 'Ventilators'
    status = Column(String(30), default="active", nullable=False)  # 'active', 'inactive'
    notes = Column(Text, nullable=True)

    vendor = relationship("Vendor", back_populates="engineers")

    def __repr__(self):
        return f"<VendorEngineer(name='{self.name}', vendor_id={self.vendor_id}, status='{self.status}')>"

