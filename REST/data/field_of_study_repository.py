from sqlalchemy.orm import Session
from sqlalchemy import select

from model.field_of_study_orm import FieldOfStudyORM


def get_field_of_study_by_id(db: Session, field_of_study_id: int):
    query = select(FieldOfStudyORM).where(FieldOfStudyORM.id == field_of_study_id)
    result = db.execute(query)
    return result.scalars().first()