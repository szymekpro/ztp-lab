from sqlalchemy.orm import Session

from data.product_repository import get_all_products, get_product_by_id


def list_products(db: Session):
    return get_all_products(db)


def get_product(db: Session, product_id: int):
    return get_product_by_id(db, product_id)
