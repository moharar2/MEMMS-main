"""
Audit service for tracking user actions, entity mutations, and security events.
"""
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from src.models.audit import AuditLog
from src.core.database import get_db



class AuditService:
    @staticmethod
    def log_action(
        db: Session,
        action: str,
        entity_name: Optional[str] = None,
        user_id: Optional[int] = None,
        entity_id: Optional[str] = None,
        details: Optional[str] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user: Optional[Any] = None,
        entity_type: Optional[str] = None
    ) -> AuditLog:
        """
        Creates an audit trail record within the current active session.
        """
        if user_id is None and user is not None:
            user_id = user.id if hasattr(user, "id") else user

        final_entity_name = entity_name or entity_type or "Unknown"

        log = AuditLog(
            user_id=user_id,
            action=action,
            entity_name=final_entity_name,
            entity_id=str(entity_id) if entity_id is not None else None,
            details=details,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address
        )
        db.add(log)
        db.flush()
        return log

    @staticmethod
    def log(
        db: Session,
        action: str,
        entity_type: str,
        entity_id: Optional[int] = None,
        user_id: Optional[int] = None,
        details: Optional[str] = None
    ) -> AuditLog:
        """Convenience wrapper used by service layer."""
        return audit_service.log_action(
            db,
            action=action,
            entity_name=entity_type,
            user_id=user_id,
            entity_id=str(entity_id) if entity_id is not None else None,
            details=details
        )


audit_service = AuditService()
