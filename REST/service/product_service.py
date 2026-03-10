# service/product_service.py
from sqlalchemy.orm import Session

from model.product_orm import ProductORM
from model.product_schema import ProductCreate, ProductUpdate
from data.product_repository import (
    add_product, delete_product, get_all_products,
    get_product_by_id, save_product,
)
from service.product_validators import (
    validate_product_name_length,
    validate_product_name_alphanumeric,
    validate_product_name_unique,
    validate_category_exists,
    validate_price_range,
    validate_quantity_non_negative,
    validate_product_name_forbidden_phrases,
)


def _validate_product_full_data(db: Session, payload: ProductCreate, product_id: int = None):
    validate_product_name_length(payload.name)
    validate_product_name_alphanumeric(payload.name)
    validate_product_name_unique(db, payload.name, product_id)
    validate_product_name_forbidden_phrases(db, payload.name)

    category = validate_category_exists(db, payload.category_id)
    validate_price_range(category, payload.price)

    validate_quantity_non_negative(payload.quantity)

    return category


def list_products(db: Session):
    return get_all_products(db)


def get_product(db: Session, product_id: int):
    return get_product_by_id(db, product_id)


def create_product(db: Session, payload: ProductCreate):
    _validate_product_full_data(db, payload)

    product = ProductORM(
        name=payload.name,
        category_id=payload.category_id,
        price=payload.price,
        quantity=payload.quantity,
    )
    return add_product(db, product)


def replace_product(db: Session, product_id: int, payload: ProductCreate):
    product = get_product_by_id(db, product_id)
    if product is None:
        return None

    _validate_product_full_data(db, payload, product_id)

    product.name = payload.name
    product.category_id = payload.category_id
    product.price = payload.price
    product.quantity = payload.quantity

    return save_product(db, product)


def patch_product(db: Session, product_id: int, payload: ProductUpdate):
    product = get_product_by_id(db, product_id)
    if product is None:
        return None

    if payload.name is not None:
        validate_product_name_length(payload.name)
        validate_product_name_alphanumeric(payload.name)
        validate_product_name_unique(db, payload.name, product_id)
        validate_product_name_forbidden_phrases(db, payload.name)
        product.name = payload.name

    category_id_to_validate = payload.category_id or product.category_id
    category = validate_category_exists(db, category_id_to_validate)

    if payload.price is not None:
        validate_price_range(category, payload.price)
        product.price = payload.price

    if payload.category_id is not None:
        if payload.price is None:
            validate_price_range(category, product.price)
        product.category_id = payload.category_id

    if payload.quantity is not None:
        validate_quantity_non_negative(payload.quantity)
        product.quantity = payload.quantity

    return save_product(db, product)


def remove_product(db: Session, product_id: int):
    product = get_product_by_id(db, product_id)
    if product is None:
        return False

    delete_product(db, product)
    return True
