from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.REST.model.product_history_orm import ProductHistoryORM


def get_product_history_by_product_id(db: Session, product_id: int):
    query = (
        select(ProductHistoryORM)
        .where(ProductHistoryORM.product_id == product_id)
        .order_by(
            desc(ProductHistoryORM.changed_at), 
            desc(ProductHistoryORM.id))
    )
    result = db.execute(query)
    return result.scalars().all()


def add_product_history(db: Session, history_entry: ProductHistoryORM):
    db.add(history_entry)
    db.commit()
    db.refresh(history_entry)
    return history_entry
