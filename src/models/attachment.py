"""
Attachment and document metadata model.
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from src.models.base import BaseModel, utc_now


class Attachment(BaseModel):
    __tablename__ = "attachments"

    entity_type = Column(String(50), nullable=False, index=True)  # 'equipment', 'work_order', 'pm_execution', 'contract'
    entity_id = Column(Integer, nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    stored_file_path = Column(String(500), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    mime_type = Column(String(100), nullable=True)
    description = Column(String(255), nullable=True)
    attachment_type = Column(String(50), default="other", nullable=True)  # 'operation_manual', 'service_manual', 'qualification', 'general'
    uploaded_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    upload_date = Column(DateTime, default=utc_now, nullable=False)

    uploaded_by = relationship("User")

    def __repr__(self):
        return f"<Attachment(entity='{self.entity_type}', id={self.entity_id}, file='{self.file_name}')>"
