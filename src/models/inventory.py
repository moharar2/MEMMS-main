"""
Spare parts, stock levels, and inventory transactions.
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from src.models.base import BaseModel, utc_now


class SparePart(BaseModel):
    __tablename__ = "spare_parts"

    part_number = Column(String(100), unique=True, nullable=False, index=True)
    name_ar = Column(String(150), nullable=False, index=True)
    name_en = Column(String(150), nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=False, index=True)

    manufacturer_id = Column(Integer, ForeignKey("vendors.id", ondelete="SET NULL"), nullable=True)
    storage_bin_location = Column(String(100), nullable=True)

    quantity_on_hand = Column(Float, default=0.0, nullable=False)
    minimum_reorder_level = Column(Float, default=5.0, nullable=False)
    unit_cost = Column(Float, default=0.0, nullable=False)
    unit_of_measure = Column(String(30), default="Piece", nullable=False)  # 'Piece', 'Kit', 'Box', 'Meter', etc.
    is_active = Column(Boolean, default=True, nullable=False)

    manufacturer = relationship("Vendor", back_populates="spare_parts")
    transactions = relationship("InventoryTransaction", back_populates="part", cascade="all, delete-orphan")

    def is_low_stock(self) -> bool:
        return self.quantity_on_hand <= self.minimum_reorder_level

    def __repr__(self):
        return f"<SparePart(part_number='{self.part_number}', name='{self.name_ar}', qty={self.quantity_on_hand})>"


class InventoryTransaction(BaseModel):
    __tablename__ = "inventory_transactions"

    part_id = Column(Integer, ForeignKey("spare_parts.id", ondelete="CASCADE"), nullable=False)
    transaction_type = Column(String(50), nullable=False)  # 'in_purchase', 'in_return', 'out_work_order', 'adjustment'
    quantity = Column(Float, nullable=False)
    unit_cost = Column(Float, default=0.0, nullable=False)
    
    work_order_id = Column(Integer, ForeignKey("work_orders.id", ondelete="SET NULL"), nullable=True)
    reference_number = Column(String(100), nullable=True)  # PO Number, invoice number, etc.
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    notes = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=utc_now, nullable=False)

    part = relationship("SparePart", back_populates="transactions")
    work_order = relationship("WorkOrder")
    user = relationship("User")

    def __repr__(self):
        return f"<InventoryTransaction(part_id={self.part_id}, type='{self.transaction_type}', qty={self.quantity})>"
