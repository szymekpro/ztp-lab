from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select

from model.product_orm import ProductORM


def get_all_products(db: Session):
    query = select(ProductORM).options(joinedload(ProductORM.category))
    result = db.execute(query)
    return result.scalars().all()


def get_product_by_id(db: Session, product_id: int):
    query = (
        select(ProductORM)
        .where(ProductORM.id == product_id)
        .options(joinedload(ProductORM.category))
    )
    result = db.execute(query)
    return result.scalars().first()


def get_product_by_name(db: Session, name: str):
    query = (
        select(ProductORM)
        .where(ProductORM.name == name)
        .options(joinedload(ProductORM.category))
    )
    result = db.execute(query)
    return result.scalars().first()


def add_product(db: Session, product: ProductORM):
    db.add(product)
    db.commit()
    return get_product_by_id(db, product.id)


def save_product(db: Session, product: ProductORM):
    db.add(product)
    db.commit()
    return get_product_by_id(db, product.id)


def delete_product(db: Session, product: ProductORM):
    db.delete(product)
    db.commit()
