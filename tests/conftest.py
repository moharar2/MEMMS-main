"""
Pytest configuration and shared test fixtures for MEMMS.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.core.database import Base
from src.models import (
    Role, User, AuditLog, Hospital, Department, Location,
    Vendor, Contract, Technician, Equipment, WorkOrder,
    WorkOrderLog, WorkOrderPart, PMPlan, PMSchedule, PMExecution,
    SparePart, InventoryTransaction, Attachment
)
from src.core.permissions import DEFAULT_ROLES
from src.core.security import hash_password


@pytest.fixture(scope="session", autouse=True)
def init_test_database():
    """
    Initialise the real database (creating all tables) once per test session.
    This ensures that UI tests that use get_db() have the tables available.
    """
    from src.core.database import init_db
    init_db()
    yield


@pytest.fixture(scope="function")
def test_db():
    """
    Creates an isolated in-memory SQLite database for each test function.
    """
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()

    # Seed roles
    for role_name, role_data in DEFAULT_ROLES.items():
        r = Role(
            name=role_name,
            display_name_ar=role_data["display_name_ar"],
            display_name_en=role_data["display_name_en"],
            permissions=role_data["permissions"],
            description=role_data["description"]
        )
        db.add(r)
    db.commit()

    # Seed admin user
    admin_role = db.query(Role).filter_by(name="admin").first()
    admin_user = User(
        username="admin",
        password_hash=hash_password("Admin@123456"),
        full_name="Admin Test",
        email="admin@test.local",
        role_id=admin_role.id,
        is_active=True
    )
    db.add(admin_user)
    db.commit()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
