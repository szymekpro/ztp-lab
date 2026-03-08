from sqlalchemy.orm import Session
from sqlalchemy import select

from model.product_orm import ProductORM


def get_all_products(db: Session):
    query = select(ProductORM)
    result = db.execute(query)
    return result.scalars().all()


def get_product_by_id(db: Session, product_id: int):
    query = select(ProductORM).where(ProductORM.id == product_id)
    result = db.execute(query)
    return result.scalars().first()
