"""
Generic Repository pattern providing standard CRUD operations over SQLAlchemy ORM.
"""
from typing import Type, TypeVar, Generic, List, Optional, Any, Dict
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from src.core.database import Base
from src.core.exceptions import NotFoundError

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    def get_by_id(self, db: Session, entity_id: Any) -> Optional[ModelType]:
        """Fetches a single record by primary key id."""
        return db.query(self.model).filter(self.model.id == entity_id).first()

    def get_by_id_or_fail(self, db: Session, entity_id: Any) -> ModelType:
        """Fetches a single record or raises NotFoundError if missing."""
        record = self.get_by_id(db, entity_id)
        if not record:
            raise NotFoundError(self.model.__name__, entity_id)
        return record

    def get_all(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        order_by: str = "id",
        descending: bool = True,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[ModelType]:
        """Fetches paginated list of records with optional filtering and ordering."""
        query = db.query(self.model)

        if filters:
            for attr, val in filters.items():
                if val is not None and hasattr(self.model, attr):
                    query = query.filter(getattr(self.model, attr) == val)

        if hasattr(self.model, order_by):
            order_col = getattr(self.model, order_by)
            query = query.order_by(desc(order_col) if descending else asc(order_col))

        return query.offset(skip).limit(limit).all()

    def count(self, db: Session, filters: Optional[Dict[str, Any]] = None) -> int:
        """Counts matching records."""
        query = db.query(self.model)
        if filters:
            for attr, val in filters.items():
                if val is not None and hasattr(self.model, attr):
                    query = query.filter(getattr(self.model, attr) == val)
        return query.count()

    def create(self, db: Session, obj_data: Dict[str, Any]) -> ModelType:
        """Instantiates and commits a new record."""
        record = self.model(**obj_data)
        db.add(record)
        db.flush()
        return record

    def update(self, db: Session, entity_id: Any, update_data: Dict[str, Any]) -> ModelType:
        """Updates an existing record by id."""
        record = self.get_by_id_or_fail(db, entity_id)
        for key, value in update_data.items():
            if hasattr(record, key) and key != "id":
                setattr(record, key, value)
        db.flush()
        return record

    def delete(self, db: Session, entity_id: Any) -> bool:
        """Deletes a record by id."""
        record = self.get_by_id_or_fail(db, entity_id)
        db.delete(record)
        db.flush()
        return True
