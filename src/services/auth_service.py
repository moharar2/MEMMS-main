"""
Authentication and user management service with RBAC enforcement.
"""
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from src.models.user import User
from src.models.role import Role
from src.core.security import hash_password, verify_password
from src.core.exceptions import AuthenticationError, PermissionDeniedError, ValidationError, NotFoundError
from src.core.permissions import check_permission, PERM_USERS_MANAGE
from src.services.audit_service import audit_service


class AuthService:
    def __init__(self):
        self._current_user: Optional[User] = None

    @property
    def current_user(self) -> Optional[User]:
        return self._current_user

    def set_current_user(self, user: Optional[User]):
        self._current_user = user

    def authenticate(self, db: Session, username: str, plain_password: str) -> User:
        """
        Authenticates a user against database records.
        Raises AuthenticationError on failure.
        """
        if not username or not plain_password:
            raise AuthenticationError("Username and password are required.")

        user = db.query(User).filter(User.username == username.strip()).first()
        if not user:
            raise AuthenticationError("Invalid username or password.")

        if not user.is_active:
            raise AuthenticationError("Account is inactive. Please contact your system administrator.")

        if not user.verify_password(plain_password):
            raise AuthenticationError("Invalid username or password.")

        # Log successful login
        audit_service.log_action(
            db=db,
            action="LOGIN",
            entity_name="User",
            user_id=user.id,
            entity_id=str(user.id),
            details=f"User '{user.username}' successfully logged in."
        )

        self._current_user = user
        return user

    def logout(self, db: Session):
        """Logs out current user."""
        if self._current_user:
            audit_service.log_action(
                db=db,
                action="LOGOUT",
                entity_name="User",
                user_id=self._current_user.id,
                entity_id=str(self._current_user.id),
                details=f"User '{self._current_user.username}' logged out."
            )
        self._current_user = None

    def create_user(self, db: Session, creator_user: User, user_data: Dict[str, Any]) -> User:
        """Creates a new user under PERM_USERS_MANAGE authorization."""
        check_permission(creator_user, PERM_USERS_MANAGE)

        username = user_data.get("username", "").strip()
        if not username:
            raise ValidationError("Username is required.")

        if db.query(User).filter(User.username == username).first():
            raise ValidationError(f"Username '{username}' is already in use.")

        role_id = user_data.get("role_id")
        if not role_id or not db.query(Role).filter(Role.id == role_id).first():
            raise ValidationError("A valid role must be selected.")

        raw_password = user_data.get("password")
        if not raw_password:
            raise ValidationError("Password is required.")

        hashed = hash_password(raw_password)

        new_user = User(
            username=username,
            password_hash=hashed,
            full_name=user_data.get("full_name", "").strip(),
            email=user_data.get("email"),
            phone=user_data.get("phone"),
            role_id=role_id,
            is_active=user_data.get("is_active", True)
        )
        db.add(new_user)
        db.flush()

        audit_service.log_action(
            db=db,
            action="CREATE",
            entity_name="User",
            user_id=creator_user.id,
            entity_id=str(new_user.id),
            details=f"Created user '{new_user.username}' with role_id {new_user.role_id}.",
            new_values={"username": new_user.username, "full_name": new_user.full_name, "role_id": new_user.role_id}
        )
        return new_user

    def change_password(self, db: Session, user: User, old_password: str, new_password: str):
        """Allows a user to change their own password."""
        if not user.verify_password(old_password):
            raise AuthenticationError("Current password is not correct.")
        
        user.set_password(new_password)
        db.flush()

        audit_service.log_action(
            db=db,
            action="CHANGE_PASSWORD",
            entity_name="User",
            user_id=user.id,
            entity_id=str(user.id),
            details=f"User '{user.username}' changed their password."
        )


auth_service = AuthService()
