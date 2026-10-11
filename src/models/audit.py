"""
AuditLog model for recording system actions and changes.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from src.models.base import BaseModel


class AuditLog(BaseModel):
    __tablename__ = "audit_logs"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(50), nullable=False, index=True)  # 'CREATE', 'UPDATE', 'DELETE', 'LOGIN', 'LOGOUT', 'EXPORT', 'BACKUP'
    entity_name = Column(String(50), nullable=False, index=True)  # e.g., 'Equipment', 'WorkOrder'
    entity_id = Column(String(50), nullable=True)
    details = Column(Text, nullable=True)
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)

    user = relationship("User", back_populates="audit_logs", lazy="joined")

    def __repr__(self):
        return f"<AuditLog(action='{self.action}', entity='{self.entity_name}', entity_id='{self.entity_id}')>"
