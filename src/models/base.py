"""
Base declarative model and common column definitions for all MEMMS tables.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, DateTime
from src.core.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class BaseModel(Base):
    """
    Abstract base model that includes primary key 'id',
    and automatic 'created_at' and 'updated_at' audit timestamps.
    """
    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    def to_dict(self) -> dict:
        """Serializes model attributes to a standard python dictionary."""
        result = {}
        for col in self.__table__.columns:
            val = getattr(self, col.name)
            if isinstance(val, datetime):
                val = val.isoformat()
            result[col.name] = val
        return result
