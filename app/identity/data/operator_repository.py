from sqlalchemy import select
from sqlalchemy.orm import Session

from app.identity.model.operator_orm import OperatorORM


def get_operator_by_email(db: Session, email: str) -> OperatorORM | None:
    query = select(OperatorORM).where(OperatorORM.email == email)
    result = db.execute(query)
    return result.scalars().first()


def get_operator_by_id(db: Session, operator_id: int) -> OperatorORM | None:
    query = select(OperatorORM).where(OperatorORM.id == operator_id)
    result = db.execute(query)
    return result.scalars().first()


def add_operator(db: Session, operator: OperatorORM) -> OperatorORM:
    db.add(operator)
    db.commit()
    db.refresh(operator)
    return operator