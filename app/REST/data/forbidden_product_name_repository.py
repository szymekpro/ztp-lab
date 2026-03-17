from sqlalchemy.orm import Session
from sqlalchemy import select

from app.REST.model.forbidden_product_name_orm import ForbiddenProductNameORM


def get_forbidden_product_phrases(db: Session):
    query = select(ForbiddenProductNameORM)
    result = db.execute(query)
    return [row.phrase for row in result.scalars().all()]
