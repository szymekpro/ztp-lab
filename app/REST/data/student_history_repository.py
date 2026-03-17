from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.REST.model.student_history_orm import StudentHistoryORM


def get_student_history_by_student_id(db: Session, student_id: int):
    query = (
        select(StudentHistoryORM)
        .where(StudentHistoryORM.student_id == student_id)
        .order_by(
            desc(StudentHistoryORM.changed_at),
            desc(StudentHistoryORM.id)
        )
    )
    result = db.execute(query)
    return result.scalars().all()


def add_student_history(db: Session, history_entry: StudentHistoryORM):
    db.add(history_entry)
    db.commit()
    db.refresh(history_entry)
    return history_entry