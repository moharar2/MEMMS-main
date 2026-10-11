"""
Core foundation package for MEMMS.
"""
from src.core.database import Base, engine, get_db, init_db, SessionLocal
from src.core.security import hash_password, verify_password, validate_password_strength
from src.core.permissions import check_permission, user_has_permission, DEFAULT_ROLES, ALL_PERMISSIONS
from src.core.exceptions import (
    MEMMSError, AuthenticationError, PermissionDeniedError,
    NotFoundError, ValidationError, InsufficientStockError, DuplicateRecordError
)
from src.core.i18n import i18n, tr

__all__ = [
    "Base", "engine", "get_db", "init_db", "SessionLocal",
    "hash_password", "verify_password", "validate_password_strength",
    "check_permission", "user_has_permission", "DEFAULT_ROLES", "ALL_PERMISSIONS",
    "MEMMSError", "AuthenticationError", "PermissionDeniedError",
    "NotFoundError", "ValidationError", "InsufficientStockError", "DuplicateRecordError",
    "i18n", "tr"
]
