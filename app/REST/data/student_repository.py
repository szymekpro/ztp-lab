from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select

from app.REST.model.student_orm import StudentORM
from app.REST.model.field_of_study_orm import FieldOfStudyORM


def get_all_students(db: Session):
    query = (
        select(StudentORM)
        .options(
            joinedload(StudentORM.field_of_study)
            .joinedload(FieldOfStudyORM.faculty)
        )
    )
    result = db.execute(query)
    return result.scalars().all()


def get_student_by_id(db: Session, student_id: int):
    query = (
        select(StudentORM)
        .where(StudentORM.id == student_id)
        .options(
            joinedload(StudentORM.field_of_study)
            .joinedload(FieldOfStudyORM.faculty)
        )
    )
    result = db.execute(query)
    return result.scalars().first()


def get_student_by_student_code(db: Session, student_code: str):
    query = (
        select(StudentORM)
        .where(StudentORM.student_code == student_code)
        .options(
            joinedload(StudentORM.field_of_study)
            .joinedload(FieldOfStudyORM.faculty)
        )
    )
    result = db.execute(query)
    return result.scalars().first()


def add_student(db: Session, student: StudentORM):
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


def save_student(db: Session, student: StudentORM):
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


def delete_student(db: Session, student: StudentORM):
    db.delete(student)
    db.commit()