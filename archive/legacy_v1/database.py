"""
database.py
-----------
Database connection setup for MEMMS.

Responsibilities:
- Define where the SQLite file lives (data/memms.db)
- Create the SQLAlchemy engine
- Provide a session factory (SessionLocal)
- Expose a small `get_session()` helper that auto-closes the session

Keeping this file small and standalone makes it easy to swap SQLite for
PostgreSQL later: only the DATABASE_URL and one or two engine options change.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------
# BASE_DIR points to the MEMMS project root (the folder that contains this
# file). data/ lives next to it.
BASE_DIR: Path = Path(__file__).resolve().parent
DATA_DIR: Path = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)  # create data/ if missing

DB_FILE: Path = DATA_DIR / "memms.db"

# SQLAlchemy URL. SQLite needs three slashes for a relative path; for an
# absolute path it needs four. We feed an absolute Path converted to a string.
DATABASE_URL: str = f"sqlite:///{DB_FILE.as_posix()}"


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------
# `check_same_thread=False` is a SQLite-specific option that lets SQLAlchemy
# use the connection from multiple threads (Qt's UI thread + background
# queries). Safe for a desktop app, kept simple for a beginner project.
engine = create_engine(
    DATABASE_URL,
    echo=False,            # set True to see every SQL statement in console
    future=True,           # use SQLAlchemy 2.x style
    connect_args={"check_same_thread": False},
)


# ---------------------------------------------------------------------------
# Declarative base
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    """Base class for all ORM models. Imported by models.py."""
    pass


# ---------------------------------------------------------------------------
# Session factory + helper
# ---------------------------------------------------------------------------
# SessionLocal is a class, not an instance. Call SessionLocal() to get a
# session. autocommit=False / autoflush=False are SQLAlchemy defaults that
# give us explicit control — easier to teach beginners.
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


@contextmanager
def get_session() -> Iterator[Session]:
    """
    Context manager that yields a SQLAlchemy Session and guarantees it is
    closed, even if an exception is raised inside the `with` block.

    Usage:
        with get_session() as session:
            count = session.query(Equipment).count()
    """
    session: Session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def _run_migrations() -> None:
    """
    Safely alter tables to add new columns if upgrading an existing SQLite database.
    Preserves all existing user records and relationships.
    """
    from sqlalchemy import inspect, text

    inspector = inspect(engine)
    if "staff" in inspector.get_table_names():
        columns = {col["name"] for col in inspector.get_columns("staff")}
        with engine.begin() as conn:
            if "staff_code" not in columns:
                conn.execute(text("ALTER TABLE staff ADD COLUMN staff_code VARCHAR(60);"))
            if "specialization" not in columns:
                conn.execute(text("ALTER TABLE staff ADD COLUMN specialization VARCHAR(120);"))
            if "phone" not in columns:
                conn.execute(text("ALTER TABLE staff ADD COLUMN phone VARCHAR(40);"))
            if "email" not in columns:
                conn.execute(text("ALTER TABLE staff ADD COLUMN email VARCHAR(120);"))
            if "hire_date" not in columns:
                conn.execute(text("ALTER TABLE staff ADD COLUMN hire_date DATE;"))
            if "notes" not in columns:
                conn.execute(text("ALTER TABLE staff ADD COLUMN notes TEXT;"))

            # Populate default staff_code for any legacy records missing one
            conn.execute(text("UPDATE staff SET staff_code = 'STF-' || id WHERE staff_code IS NULL OR staff_code = '';"))
            # Ensure unique index exists on staff_code
            conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_staff_staff_code ON staff(staff_code);"))

def _seed_initial_data() -> None:
    """Seed initial hospital departments if the departments table is empty."""
    from models import Department
    with get_session() as session:
        if session.query(Department).count() == 0:
            default_departments = [
                Department(name_ar="الهندسة الطبية الحيوية", name_en="Biomedical Engineering", location="B-101"),
                Department(name_ar="العناية المركزة (ICU)", name_en="Intensive Care Unit (ICU)", location="A-201"),
                Department(name_ar="العمليات الجراحية (OR)", name_en="Operating Theater (OR)", location="A-301"),
                Department(name_ar="الأشعة والتصوير الطبي", name_en="Radiology & Imaging", location="B-001"),
                Department(name_ar="المختبر الطبي", name_en="Clinical Laboratory", location="C-101"),
                Department(name_ar="طوارئ الحوادث (ER)", name_en="Emergency Department (ER)", location="A-101"),
            ]
            session.add_all(default_departments)
            session.commit()

def init_db() -> None:
    """
    Create all tables defined on Base.metadata and apply non-destructive migrations.
    Safe to call repeatedly — existing tables and rows are preserved.
    """
    # Importing models here ensures all model classes are registered on
    # Base.metadata before create_all runs.
    from models import (  # noqa: F401  (import for side-effect)
        Department,
        Equipment,
        MaintenancePlan,
        SparePart,
        Staff,
        WorkOrder,
        WorkOrderPart,
    )
    Base.metadata.create_all(bind=engine)
    _run_migrations()
    _seed_initial_data()


if __name__ == "__main__":
    # Tiny self-test: print where the DB lives and create tables.
    print(f"Database file: {DB_FILE}")
    init_db()
    print("Tables created (or already existed).")
