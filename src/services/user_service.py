"""
Enterprise User & RBAC Management Service.
Handles user lifecycle, role assignments, security guardrails, password resets, and comprehensive audit logging.
Pure Arabic RTL enterprise security framework.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from src.models.user import User
from src.models.role import Role
from src.core.security import hash_password
from src.core.exceptions import (
    ValidationError, NotFoundError, DuplicateRecordError,
    PermissionDeniedError, AuthenticationError
)
from src.core.permissions import (
    check_permission, is_admin, PERM_USERS_MANAGE
)
from src.services.audit_service import audit_service


class UserService:
    def list_users(
        self,
        db: Session,
        search_query: Optional[str] = None,
        role_id: Optional[int] = None,
        is_active: Optional[bool] = None
    ) -> List[User]:
        """
        Queries and filters users with optional role and status criteria.
        """
        query = db.query(User)

        if role_id:
            query = query.filter(User.role_id == role_id)
        if is_active is not None:
            query = query.filter(User.is_active == is_active)

        if search_query:
            term = f"%{search_query.strip()}%"
            query = query.filter(
                or_(
                    User.username.ilike(term),
                    User.full_name.ilike(term),
                    User.email.ilike(term),
                    User.phone.ilike(term)
                )
            )

        return query.order_by(User.id.asc()).all()

    def get_user_by_id(self, db: Session, user_id: int) -> User:
        """
        Retrieves a user by ID or raises NotFoundError.
        """
        user = db.query(User).filter_by(id=user_id).first()
        if not user:
            raise NotFoundError("User", user_id)
        return user

    def get_user_by_username(self, db: Session, username: str) -> Optional[User]:
        """
        Retrieves a user by exact username.
        """
        if not username:
            return None
        return db.query(User).filter(User.username == username.strip()).first()

    def get_user_stats(self, db: Session) -> Dict[str, int]:
        """
        Calculates aggregate user metrics for dashboard and KPI cards.
        """
        total = db.query(func.count(User.id)).scalar() or 0
        active = db.query(func.count(User.id)).filter(User.is_active == True).scalar() or 0
        inactive = total - active

        # Admins count
        admins = db.query(func.count(User.id)).join(Role).filter(
            Role.name == "admin", User.is_active == True
        ).scalar() or 0

        # Technical / Engineering staff count
        tech_staff = db.query(func.count(User.id)).join(Role).filter(
            Role.name.in_(["biomedical_engineer", "engineer", "technician"]),
            User.is_active == True
        ).scalar() or 0

        return {
            "total": total,
            "active": active,
            "inactive": inactive,
            "admins": admins,
            "technical": tech_staff
        }

    def list_roles(self, db: Session) -> List[Role]:
        """
        Retrieves all available roles in the system.
        """
        return db.query(Role).order_by(Role.id.asc()).all()

    def get_role_by_id(self, db: Session, role_id: int) -> Role:
        """
        Retrieves a role by ID or raises NotFoundError.
        """
        role = db.query(Role).filter_by(id=role_id).first()
        if not role:
            raise NotFoundError("Role", role_id)
        return role

    def count_active_admins(self, db: Session, exclude_user_id: Optional[int] = None) -> int:
        """
        Counts active system administrators, optionally excluding a specific user ID.
        """
        query = db.query(func.count(User.id)).join(Role).filter(
            Role.name == "admin",
            User.is_active == True
        )
        if exclude_user_id:
            query = query.filter(User.id != exclude_user_id)
        return query.scalar() or 0

    def create_user(self, db: Session, current_user: User, user_data: Dict[str, Any]) -> User:
        """
        Creates a new user with validation, permission enforcement, and audit logging.
        """
        check_permission(current_user, PERM_USERS_MANAGE)

        username = (user_data.get("username") or "").strip()
        if not username:
            raise ValidationError("اسم المستخدم مطلوب ولا يمكن أن يكون فارغاً.")
        if len(username) < 3:
            raise ValidationError("يجب أن يتكون اسم المستخدم من 3 أحرف على الأقل.")

        if db.query(User).filter(User.username == username).first():
            raise DuplicateRecordError(f"اسم المستخدم '{username}' مستخدم بالفعل، يرجى اختيار اسم آخر.")

        full_name = (user_data.get("full_name") or "").strip()
        if not full_name:
            raise ValidationError("الاسم الكامل للمستخدم مطلوب.")

        role_id = user_data.get("role_id")
        if not role_id:
            raise ValidationError("يجب اختيار الدور الوظيفي للمستخدم.")
        
        target_role = db.query(Role).filter_by(id=role_id).first()
        if not target_role:
            raise ValidationError("الدور الوظيفي المحدد غير موجود.")

        # Guardrail: Non-admin cannot assign admin role
        if target_role.name == "admin" and not is_admin(current_user):
            raise PermissionDeniedError("لا يمكن لغير مدير النظام منح صلاحيات مدير النظام لمستخدم آخر.")

        raw_password = user_data.get("password")
        if not raw_password or len(raw_password) < 6:
            raise ValidationError("كلمة المرور مطلوبة ويجب أن تتكون من 6 خانات على الأقل.")

        new_user = User(
            username=username,
            password_hash=hash_password(raw_password),
            full_name=full_name,
            email=(user_data.get("email") or "").strip() or None,
            phone=(user_data.get("phone") or "").strip() or None,
            role_id=role_id,
            is_active=bool(user_data.get("is_active", True))
        )
        db.add(new_user)
        db.flush()

        audit_service.log_action(
            db=db,
            action="CREATE",
            entity_name="User",
            user_id=current_user.id if current_user else None,
            entity_id=str(new_user.id),
            details=f"تم إنشاء حساب المستخدم '{new_user.username}' باسم '{new_user.full_name}' ودور '{target_role.display_name_ar}'.",
            new_values={
                "username": new_user.username,
                "full_name": new_user.full_name,
                "role": target_role.name,
                "is_active": new_user.is_active
            }
        )

        return new_user

    def update_user(self, db: Session, current_user: User, user_id: int, user_data: Dict[str, Any]) -> User:
        """
        Updates an existing user account with safety guardrails.
        """
        check_permission(current_user, PERM_USERS_MANAGE)

        target_user = self.get_user_by_id(db, user_id)
        old_role = target_user.role

        full_name = (user_data.get("full_name") or "").strip()
        if not full_name:
            raise ValidationError("الاسم الكامل مطلوب.")

        role_id = user_data.get("role_id", target_user.role_id)
        new_role = db.query(Role).filter_by(id=role_id).first()
        if not new_role:
            raise ValidationError("الدور الوظيفي المحدد غير موجود.")

        # Guardrail: Non-admin cannot assign admin role
        if new_role.name == "admin" and not is_admin(current_user):
            raise PermissionDeniedError("لا يمكن لغير مدير النظام ترقية المستخدمين إلى رتبة مدير النظام.")

        is_active = bool(user_data.get("is_active", target_user.is_active))

        # Guardrail: Prevent deactivating or demoting the LAST active admin
        if old_role and old_role.name == "admin" and target_user.is_active:
            if not is_active or new_role.name != "admin":
                active_admins_remaining = self.count_active_admins(db, exclude_user_id=target_user.id)
                if active_admins_remaining == 0:
                    raise ValidationError("لا يمكن تعطيل أو تغيير دور آخر مدير نظام نشط للحفاظ على إمكانية إدارة المنظومة.")

        # Check optional username change
        if "username" in user_data:
            new_username = user_data["username"].strip()
            if new_username and new_username != target_user.username:
                if db.query(User).filter(User.username == new_username, User.id != user_id).first():
                    raise DuplicateRecordError(f"اسم المستخدم '{new_username}' مستخدم بالفعل.")
                target_user.username = new_username

        target_user.full_name = full_name
        target_user.email = (user_data.get("email") or "").strip() or None
        target_user.phone = (user_data.get("phone") or "").strip() or None
        target_user.role_id = role_id
        target_user.is_active = is_active
        db.flush()

        audit_service.log_action(
            db=db,
            action="UPDATE",
            entity_name="User",
            user_id=current_user.id if current_user else None,
            entity_id=str(target_user.id),
            details=f"تم تعديل بيانات المستخدم '{target_user.username}' (الدور: {new_role.display_name_ar}، الحالة: {'نشط' if is_active else 'معطل'}).",
            new_values={
                "username": target_user.username,
                "full_name": target_user.full_name,
                "role": new_role.name,
                "is_active": target_user.is_active
            }
        )

        return target_user

    def toggle_user_status(self, db: Session, current_user: User, user_id: int, is_active: bool) -> User:
        """
        Enables or disables a user account with protection for the last admin.
        """
        check_permission(current_user, PERM_USERS_MANAGE)

        target_user = self.get_user_by_id(db, user_id)

        if not is_active and target_user.is_active and target_user.role and target_user.role.name == "admin":
            if self.count_active_admins(db, exclude_user_id=target_user.id) == 0:
                raise ValidationError("لا يمكن تعطيل آخر مدير نظام نشط في المنظومة.")

        target_user.is_active = is_active
        db.flush()

        action_name = "ACTIVATE" if is_active else "DEACTIVATE"
        status_text = "تنشيط" if is_active else "تعطيل"

        audit_service.log_action(
            db=db,
            action=action_name,
            entity_name="User",
            user_id=current_user.id if current_user else None,
            entity_id=str(target_user.id),
            details=f"تم {status_text} حساب المستخدم '{target_user.username}'."
        )

        return target_user

    def reset_password(self, db: Session, current_user: User, user_id: int, new_password: str) -> None:
        """
        Resets the password for a user account with validation and audit trail.
        """
        check_permission(current_user, PERM_USERS_MANAGE)

        if not new_password or len(new_password) < 6:
            raise ValidationError("كلمة المرور الجديدة يجب ألا تقل عن 6 خانات.")

        target_user = self.get_user_by_id(db, user_id)
        target_user.password_hash = hash_password(new_password)
        db.flush()

        audit_service.log_action(
            db=db,
            action="RESET_PASSWORD",
            entity_name="User",
            user_id=current_user.id if current_user else None,
            entity_id=str(target_user.id),
            details=f"قام '{current_user.username}' بإعادة تعيين كلمة المرور للمستخدم '{target_user.username}'."
        )

    def update_role_permissions(
        self,
        db: Session,
        current_user: User,
        role_id: int,
        permissions: List[str]
    ) -> Role:
        """
        Updates permissions assigned to a role.
        """
        check_permission(current_user, PERM_USERS_MANAGE)
        if not is_admin(current_user):
            raise PermissionDeniedError("تعديل الصلاحيات متاح فقط لمدير النظام.")

        role = self.get_role_by_id(db, role_id)
        role.permissions = list(set(permissions))
        db.flush()

        audit_service.log_action(
            db=db,
            action="UPDATE_PERMISSIONS",
            entity_name="Role",
            user_id=current_user.id if current_user else None,
            entity_id=str(role.id),
            details=f"تم تحديث صلاحيات الدور '{role.display_name_ar}' بإجمالي ({len(role.permissions)}) صلاحية."
        )

        return role


user_service = UserService()
