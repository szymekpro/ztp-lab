from sqlalchemy.orm import Session
from data.student_repository import get_all_students


def list_students(db: Session):
    return get_all_students(db)