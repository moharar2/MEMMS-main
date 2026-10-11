"""
Database session management, engine configuration, and SQLite WAL/FK pragmas.
Supports seamless migration to PostgreSQL or other SQL dialects.
"""
from contextlib import contextmanager
from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.engine import Engine
import config

# Create Base for all declarative models
Base = declarative_base()

# Configure Engine
connect_args = {}
if config.DATABASE_URL.startswith("sqlite"):
    # SQLite-specific connection arguments
    connect_args["check_same_thread"] = False

engine = create_engine(
    config.DATABASE_URL,
    echo=False,
    connect_args=connect_args,
    pool_pre_ping=True
)

# Enable Foreign Keys and Write-Ahead Logging (WAL) for SQLite
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if config.DATABASE_URL.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys=ON;")
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("PRAGMA synchronous=NORMAL;")
        finally:
            cursor.close()

# Session Factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)


@contextmanager
def get_db():
    """
    Context manager providing a transactional database session scope.
    Automatically commits on normal completion or rolls back on exception.
    """
    session: Session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def apply_schema_migrations(target_engine: Engine):
    """
    Applies non-destructive schema migrations (e.g. adding new columns to existing SQLite tables)
    without dropping or recreating any existing tables or data.
    """
    inspector = inspect(target_engine)
    existing_tables = inspector.get_table_names()

    with target_engine.connect() as conn:
        # 1. attachments.attachment_type
        if "attachments" in existing_tables:
            columns = [c["name"] for c in inspector.get_columns("attachments")]
            if "attachment_type" not in columns:
                conn.execute(text("ALTER TABLE attachments ADD COLUMN attachment_type VARCHAR(50) DEFAULT 'other'"))

        # 2. equipment.assigned_engineer_id
        if "equipment" in existing_tables:
            columns = [c["name"] for c in inspector.get_columns("equipment")]
            if "assigned_engineer_id" not in columns:
                conn.execute(text("ALTER TABLE equipment ADD COLUMN assigned_engineer_id INTEGER REFERENCES vendor_engineers(id)"))

        # 3. technicians extended columns
        if "technicians" in existing_tables:
            columns = [c["name"] for c in inspector.get_columns("technicians")]
            tech_new_cols = [
                ("nationality", "VARCHAR(50)"),
                ("id_document_type", "VARCHAR(50) DEFAULT 'national_id'"),
                ("id_number", "VARCHAR(50)"),
                ("job_title", "VARCHAR(100)"),
                ("department_id", "INTEGER REFERENCES departments(id)"),
                ("work_entity", "VARCHAR(150)"),
                ("hire_date", "DATE")
            ]
            for col_name, col_type in tech_new_cols:
                if col_name not in columns:
                    conn.execute(text(f"ALTER TABLE technicians ADD COLUMN {col_name} {col_type}"))

        conn.commit()


def init_db(engine_override: Engine = None):
    """
    Initializes database schema and ensures default roles and demo accounts exist.
    Preserves all existing data without schema loss.
    """
    # Import all models so metadata is populated
    import src.models  # noqa: F401
    from src.core.permissions import DEFAULT_ROLES
    from src.models.role import Role
    from src.models.user import User
    from src.core.security import hash_password

    target_engine = engine_override or engine
    Base.metadata.create_all(bind=target_engine)
    apply_schema_migrations(target_engine)

    # Use session factory bound to the target engine
    factory = sessionmaker(bind=target_engine, expire_on_commit=False)
    with factory() as db:
        # Seed or sync default roles
        for role_name, role_data in DEFAULT_ROLES.items():
            existing_role = db.query(Role).filter_by(name=role_name).first()
            if not existing_role:
                new_role = Role(
                    name=role_name,
                    display_name_ar=role_data["display_name_ar"],
                    display_name_en=role_data["display_name_en"],
                    permissions=role_data["permissions"],
                    description=role_data["description"]
                )
                db.add(new_role)
            else:
                # Keep Arabic display names up to date
                existing_role.display_name_ar = role_data["display_name_ar"]
                existing_role.display_name_en = role_data["display_name_en"]
                existing_role.description = role_data["description"]
        db.commit()

        # Seed initial admin user if no users exist
        admin_count = db.query(User).count()
        if admin_count == 0:
            admin_role = db.query(Role).filter_by(name="admin").first()
            initial_admin = User(
                username="admin",
                password_hash=hash_password("Admin@123456"),
                full_name="مدير النظام الرئيسي",
                email="admin@memms.local",
                phone="+967 1 246966",
                role_id=admin_role.id if admin_role else 1,
                is_active=True
            )
            db.add(initial_admin)
            db.commit()
            print("[DB] Initialized database and seeded default 'admin' user.")

