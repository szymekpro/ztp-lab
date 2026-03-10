from sqlalchemy.orm import Session
from sqlalchemy import select

from model.category_orm import CategoryORM


def get_category_by_id(db: Session, category_id: int):
    query = select(CategoryORM).where(CategoryORM.id == category_id)
    result = db.execute(query)
    return result.scalars().first()
