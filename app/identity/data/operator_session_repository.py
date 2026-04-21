from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.identity.model.operator_session_orm import OperatorSessionORM


def add_operator_session(db: Session, session: OperatorSessionORM) -> OperatorSessionORM:
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_session_by_token(db: Session, session_token: str) -> OperatorSessionORM | None:
    query = select(OperatorSessionORM).where(
        OperatorSessionORM.session_token == session_token
    )
    result = db.execute(query)
    return result.scalars().first()


def update_session_last_used(db: Session, session: OperatorSessionORM) -> OperatorSessionORM:
    session.last_used_at = datetime.now()
    db.commit()
    db.refresh(session)
    return session


def delete_session_by_token(db: Session, session_token: str) -> bool:
    query = delete(OperatorSessionORM).where(
        OperatorSessionORM.session_token == session_token
    )
    result = db.execute(query)
    db.commit()
    return result.rowcount > 0

def delete_session_by_id(db: Session, session_id: int) -> bool:
    query = delete(OperatorSessionORM).where(
        OperatorSessionORM.id == session_id
    )
    result = db.execute(query)
    db.commit()
    return result.rowcount > 0