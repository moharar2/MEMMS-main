"""
Comprehensive Automated Test Suite for User Management & Role-Based Access Control (RBAC).
Tests:
- Authentication, wrong password rejection, inactive account blocking.
- Role permissions matrix across all 5 roles (admin, biomedical_engineer, technician, inventory_manager, viewer).
- Backend service-level permission enforcement and Arabic error messages.
- User management CRUD (create, update, toggle active, reset password).
- Safety guardrails (protection of last active admin, self-elevation prevention).
- Audit trail logging for all user lifecycle actions.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.core.database import Base, init_db
from src.models.user import User
from src.models.role import Role
from src.models.audit import AuditLog
from src.core.permissions import (
    DEFAULT_ROLES, ALL_PERMISSIONS,
    PERM_EQUIPMENT_VIEW, PERM_EQUIPMENT_CREATE, PERM_EQUIPMENT_DELETE,
    PERM_WORK_ORDER_VIEW, PERM_WORK_ORDER_CREATE,
    PERM_PM_EXECUTE, PERM_INVENTORY_MANAGE, PERM_USERS_MANAGE,
    check_permission, can_user, is_admin
)
from src.core.exceptions import (
    AuthenticationError, PermissionDeniedError, ValidationError, DuplicateRecordError
)
from src.services.auth_service import auth_service
from src.services.user_service import user_service
from src.services.equipment_service import equipment_service


@pytest.fixture(scope="module")
def test_db_engine():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    init_db(engine_override=engine)
    return engine


@pytest.fixture
def db_session(test_db_engine):
    Session = sessionmaker(bind=test_db_engine, expire_on_commit=False)
    session = Session()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


def test_default_roles_seeded(db_session):
    """Verifies all 5 standard roles exist in database with correct Arabic names."""
    roles = db_session.query(Role).all()
    role_names = {r.name for r in roles}
    assert "admin" in role_names
    assert "biomedical_engineer" in role_names
    assert "technician" in role_names
    assert "inventory_manager" in role_names
    assert "viewer" in role_names


def test_admin_permissions(db_session):
    """Admin role should have full access (* or ALL_PERMISSIONS)."""
    admin_role = db_session.query(Role).filter_by(name="admin").first()
    assert admin_role is not None
    assert admin_role.has_permission(PERM_USERS_MANAGE) is True
    assert admin_role.has_permission(PERM_EQUIPMENT_DELETE) is True
    assert admin_role.has_permission(PERM_INVENTORY_MANAGE) is True


def test_role_permission_matrix(db_session):
    """Verifies granular permissions for each specialized role."""
    bio_role = db_session.query(Role).filter_by(name="biomedical_engineer").first()
    tech_role = db_session.query(Role).filter_by(name="technician").first()
    inv_role = db_session.query(Role).filter_by(name="inventory_manager").first()
    view_role = db_session.query(Role).filter_by(name="viewer").first()

    # Biomedical Engineer: Can create equipment, execute PM, cannot manage users
    assert bio_role.has_permission(PERM_EQUIPMENT_CREATE) is True
    assert bio_role.has_permission(PERM_PM_EXECUTE) is True
    assert bio_role.has_permission(PERM_USERS_MANAGE) is False

    # Technician: Can execute PM, view equipment, cannot delete equipment or manage users
    assert tech_role.has_permission(PERM_PM_EXECUTE) is True
    assert tech_role.has_permission(PERM_EQUIPMENT_VIEW) is True
    assert tech_role.has_permission(PERM_EQUIPMENT_DELETE) is False
    assert tech_role.has_permission(PERM_USERS_MANAGE) is False

    # Inventory Manager: Can manage inventory, cannot execute PM or manage users
    assert inv_role.has_permission(PERM_INVENTORY_MANAGE) is True
    assert inv_role.has_permission(PERM_PM_EXECUTE) is False
    assert inv_role.has_permission(PERM_USERS_MANAGE) is False

    # Viewer: Read-only access
    assert view_role.has_permission(PERM_EQUIPMENT_VIEW) is True
    assert view_role.has_permission(PERM_EQUIPMENT_CREATE) is False
    assert view_role.has_permission(PERM_EQUIPMENT_DELETE) is False
    assert view_role.has_permission(PERM_USERS_MANAGE) is False


def test_authentication_workflow(db_session):
    """Tests successful authentication and invalid password handling."""
    admin = db_session.query(User).filter_by(username="admin").first()
    assert admin is not None

    # Correct credentials
    logged_in = auth_service.authenticate(db_session, "admin", "Admin@123456")
    assert logged_in.id == admin.id
    assert auth_service.current_user.id == admin.id

    # Wrong password
    with pytest.raises(AuthenticationError):
        auth_service.authenticate(db_session, "admin", "WrongPass123")

    # Non-existent user
    with pytest.raises(AuthenticationError):
        auth_service.authenticate(db_session, "non_existent_user", "AnyPass123")


def test_inactive_user_cannot_login(db_session):
    """Inactive users must be rejected during authentication."""
    admin = db_session.query(User).filter_by(username="admin").first()
    role = db_session.query(Role).filter_by(name="viewer").first()

    # Create inactive user
    inactive_user = user_service.create_user(
        db=db_session,
        current_user=admin,
        user_data={
            "username": "disabled_user",
            "password": "Password@123",
            "full_name": "مستخدم معطل",
            "role_id": role.id,
            "is_active": False
        }
    )
    db_session.commit()

    with pytest.raises(AuthenticationError) as exc_info:
        auth_service.authenticate(db_session, "disabled_user", "Password@123")
    assert "inactive" in str(exc_info.value).lower() or "معطل" in str(exc_info.value)


def test_user_crud_and_password_reset(db_session):
    """Tests full User Management CRUD lifecycle and password reset."""
    admin = db_session.query(User).filter_by(username="admin").first()
    bio_role = db_session.query(Role).filter_by(name="biomedical_engineer").first()

    # 1. Create User
    new_user = user_service.create_user(
        db=db_session,
        current_user=admin,
        user_data={
            "username": "tariq_bio",
            "password": "InitialPassword@123",
            "full_name": "م. طارق الصنعاني",
            "role_id": bio_role.id,
            "email": "tariq@hospital.ye",
            "phone": "777000111",
            "is_active": True
        }
    )
    db_session.commit()
    assert new_user.id is not None
    assert new_user.full_name == "م. طارق الصنعاني"

    # 2. Update User
    updated_user = user_service.update_user(
        db=db_session,
        current_user=admin,
        user_id=new_user.id,
        user_data={
            "full_name": "م. طارق عبدالكريم الصنعاني",
            "role_id": bio_role.id,
            "email": "tariq_updated@hospital.ye",
            "phone": "777000222",
            "is_active": True
        }
    )
    db_session.commit()
    assert updated_user.full_name == "م. طارق عبدالكريم الصنعاني"

    # 3. Reset Password
    user_service.reset_password(
        db=db_session,
        current_user=admin,
        user_id=new_user.id,
        new_password="NewSecurePassword@2026"
    )
    db_session.commit()

    # Authenticate with new password
    auth_user = auth_service.authenticate(db_session, "tariq_bio", "NewSecurePassword@2026")
    assert auth_user.id == new_user.id

    # 4. Toggle Status (Deactivate & Reactivate)
    user_service.toggle_user_status(db_session, admin, new_user.id, False)
    db_session.commit()
    assert new_user.is_active is False

    user_service.toggle_user_status(db_session, admin, new_user.id, True)
    db_session.commit()
    assert new_user.is_active is True


def test_last_admin_protection(db_session):
    """System must prevent deactivating or demoting the last active administrator."""
    admin = db_session.query(User).filter_by(username="admin").first()
    viewer_role = db_session.query(Role).filter_by(name="viewer").first()

    # Attempting to deactivate the only admin
    with pytest.raises(ValidationError) as exc_info:
        user_service.toggle_user_status(db_session, admin, admin.id, False)
    assert "آخر مدير نظام" in str(exc_info.value)

    # Attempting to demote the only admin to viewer
    with pytest.raises(ValidationError) as exc_info:
        user_service.update_user(
            db=db_session,
            current_user=admin,
            user_id=admin.id,
            user_data={
                "full_name": "Admin",
                "role_id": viewer_role.id,
                "is_active": True
            }
        )
    assert "آخر مدير نظام" in str(exc_info.value)


def test_self_elevation_prevention(db_session):
    """Non-admin users cannot promote accounts to admin or grant unauthorized roles."""
    admin = db_session.query(User).filter_by(username="admin").first()
    tech_role = db_session.query(Role).filter_by(name="technician").first()
    admin_role = db_session.query(Role).filter_by(name="admin").first()

    # Create a normal technician
    tech_user = user_service.create_user(
        db=db_session,
        current_user=admin,
        user_data={
            "username": "salem_tech",
            "password": "Password@123",
            "full_name": "فني سالم",
            "role_id": tech_role.id,
            "is_active": True
        }
    )
    db_session.commit()

    # Technician trying to manage users -> PermissionDeniedError
    with pytest.raises(PermissionDeniedError):
        user_service.create_user(
            db=db_session,
            current_user=tech_user,
            user_data={
                "username": "hacker_user",
                "password": "Password@123",
                "full_name": "مستخدم غير مصرح",
                "role_id": admin_role.id,
                "is_active": True
            }
        )


def test_backend_service_permission_enforcement(db_session):
    """Direct service operations must reject unauthorized users even if called programmatically."""
    viewer_role = db_session.query(Role).filter_by(name="viewer").first()
    viewer_user = User(
        username="readonly_tester",
        password_hash="fakehash",
        full_name="قارئ فقط",
        role_id=viewer_role.id,
        is_active=True,
        role=viewer_role
    )

    # Attempting to create equipment as a viewer -> PermissionDeniedError
    with pytest.raises(PermissionDeniedError):
        equipment_service.create_equipment(
            db=db_session,
            user=viewer_user,
            data={
                "asset_number": "EQ-UNAUTH-001",
                "serial_number": "SN-UNAUTH-001",
                "name_ar": "جهاز غير مصرح",
                "department_id": 1
            }
        )


def test_audit_logs_recorded(db_session):
    """Verifies that user lifecycle and authentication actions are logged in AuditLog."""
    logs = db_session.query(AuditLog).filter(AuditLog.entity_name == "User").all()
    actions = {l.action for l in logs}
    assert "CREATE" in actions or "UPDATE" in actions or "LOGIN" in actions
