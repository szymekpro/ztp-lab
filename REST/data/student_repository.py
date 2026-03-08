from sqlalchemy.orm import Session
from sqlalchemy import select

from model.student_orm import StudentORM
from data.database import Base, engine


def create_tables():
    Base.metadata.create_all(engine)


def get_all_students(db: Session):
    query = select(StudentORM)
    result = db.execute(query) #(<StudentORM object>,))
    return result.scalars().all()