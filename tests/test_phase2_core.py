"""
Unit and integration tests for Phase 2:
Database initialization, RBAC permissions, Security, i18n, Theme, and Authentication.
"""
import pytest
from src.models.user import User
from src.models.role import Role
from src.models.audit import AuditLog
from src.core.security import hash_password, verify_password, validate_password_strength
from src.core.permissions import check_permission, user_has_permission, PERM_EQUIPMENT_VIEW, PERM_USERS_MANAGE
from src.core.exceptions import AuthenticationError, PermissionDeniedError
from src.core.i18n import i18n, tr
from src.ui.theme.theme_manager import theme_manager
from src.services.auth_service import auth_service


def test_password_hashing_and_verification():
    raw_pass = "SecurePass@2026"
    hashed = hash_password(raw_pass)
    assert hashed != raw_pass
    assert verify_password(raw_pass, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

    valid, _ = validate_password_strength("Short")
    assert valid is False
    valid, _ = validate_password_strength("ValidLongPassword")
    assert valid is True


def test_role_seeding_and_permissions(test_db):
    roles = test_db.query(Role).all()
    assert len(roles) >= 5
    role_names = [r.name for r in roles]
    assert "admin" in role_names
    assert "technician" in role_names
    assert "maintenance_manager" in role_names

    admin_role = test_db.query(Role).filter_by(name="admin").first()
    assert admin_role.has_permission(PERM_USERS_MANAGE) is True

    tech_role = test_db.query(Role).filter_by(name="technician").first()
    assert tech_role.has_permission(PERM_USERS_MANAGE) is False
    assert tech_role.has_permission(PERM_EQUIPMENT_VIEW) is True


def test_rbac_check_permission(test_db):
    admin_user = test_db.query(User).filter_by(username="admin").first()
    # Admin should not raise
    check_permission(admin_user, PERM_USERS_MANAGE)

    # Inactive user raises PermissionDeniedError
    admin_user.is_active = False
    with pytest.raises(PermissionDeniedError):
        check_permission(admin_user, PERM_USERS_MANAGE)


def test_auth_service_flow(test_db):
    # Authenticate valid admin
    user = auth_service.authenticate(test_db, "admin", "Admin@123456")
    assert user is not None
    assert user.username == "admin"
    assert auth_service.current_user.id == user.id

    # Verify audit log was recorded
    login_log = test_db.query(AuditLog).filter_by(action="LOGIN", user_id=user.id).first()
    assert login_log is not None

    # Authenticate with wrong password
    with pytest.raises(AuthenticationError):
        auth_service.authenticate(test_db, "admin", "WrongPass123")

    # Logout
    auth_service.logout(test_db)
    assert auth_service.current_user is None


def test_i18n_arabic_rtl_localization():
    assert i18n.current_locale == "ar"
    assert i18n.is_rtl() is True
    assert tr("app.title") == "نظام إدارة صيانة الأجهزة الطبية"
    assert tr("common.save") == "حفظ"


def test_theme_manager_qss_generation():
    theme_manager.set_theme("light")
    light_qss = theme_manager.generate_qss()
    assert "QMainWindow" in light_qss
    assert "#0F766E" in light_qss  # Enterprise Light primary color


def test_init_db_and_sqlite_pragmas(tmp_path, monkeypatch):
    from sqlalchemy import text
    import config
    from src.core.database import engine, init_db, get_db, Base
    from src.models.user import User
    from src.models.role import Role

    # Point to a temporary db file
    temp_db_path = tmp_path / "test_memms.db"
    monkeypatch.setattr(config, "DATABASE_URL", f"sqlite:///{temp_db_path.as_posix()}")

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    test_engine = create_engine(f"sqlite:///{temp_db_path.as_posix()}")

    init_db(engine_override=test_engine)

    SessionTest = sessionmaker(bind=test_engine)
    with SessionTest() as db:
        # Check SQLite Pragmas
        fk_on = db.execute(text("PRAGMA foreign_keys;")).scalar()
        assert fk_on == 1

        # Check seeded admin
        admin = db.query(User).filter_by(username="admin").first()
        assert admin is not None
        assert admin.verify_password("Admin@123456") is True

        # Check roles count
        roles_count = db.query(Role).count()
        assert roles_count >= 5
