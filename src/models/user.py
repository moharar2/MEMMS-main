"""
User model for authentication, profile data, and role association.
"""
from sqlalchemy import Column, String, Boolean, Integer, ForeignKey
from sqlalchemy.orm import relationship
from src.models.base import BaseModel
from src.core.security import verify_password, hash_password


class User(BaseModel):
    __tablename__ = "users"

    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, nullable=True)
    phone = Column(String(30), nullable=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    role = relationship("Role", back_populates="users", lazy="joined")
    audit_logs = relationship("AuditLog", back_populates="user", lazy="select")
    technician_profile = relationship("Technician", back_populates="user", uselist=False, lazy="select")

    def verify_password(self, plain_password: str) -> bool:
        """Verifies the plain password against the stored bcrypt hash."""
        return verify_password(plain_password, self.password_hash)

    def set_password(self, plain_password: str):
        """Hashes and sets the password."""
        self.password_hash = hash_password(plain_password)

    def has_permission(self, permission_name: str) -> bool:
        """Checks if the user's role has the specified permission."""
        if not self.is_active or not self.role:
            return False
        return self.role.has_permission(permission_name)

    def __repr__(self):
        return f"<User(username='{self.username}', full_name='{self.full_name}', active={self.is_active})>"
