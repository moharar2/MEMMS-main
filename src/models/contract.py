"""
Contract and warranty management models.
"""
from sqlalchemy import Column, String, Integer, Float, Date, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from src.models.base import BaseModel


class Contract(BaseModel):
    __tablename__ = "contracts"

    vendor_id = Column(Integer, ForeignKey("vendors.id", ondelete="RESTRICT"), nullable=False)
    contract_number = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(150), nullable=False)
    contract_type = Column(String(50), nullable=False, default="maintenance")  # 'maintenance', 'warranty', 'supply', 'turnkey'
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    cost = Column(Float, default=0.0, nullable=False)
    terms = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    vendor = relationship("Vendor", back_populates="contracts")

    def __repr__(self):
        return f"<Contract(number='{self.contract_number}', title='{self.title}')>"
