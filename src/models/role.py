"""
Role model representing user roles and associated RBAC permissions.
"""
from sqlalchemy import Column, String, Text, JSON
from sqlalchemy.orm import relationship
from src.models.base import BaseModel


class Role(BaseModel):
    __tablename__ = "roles"

    name = Column(String(50), unique=True, nullable=False, index=True)
    display_name_ar = Column(String(100), nullable=False)
    display_name_en = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    permissions = Column(JSON, default=list, nullable=False)  # List of permission strings

    users = relationship("User", back_populates="role", lazy="select")

    def has_permission(self, permission_name: str) -> bool:
        if not self.permissions:
            return False
        if "*" in self.permissions:
            return True
        return permission_name in self.permissions

    def __repr__(self):
        return f"<Role(name='{self.name}', display_name_ar='{self.display_name_ar}')>"
