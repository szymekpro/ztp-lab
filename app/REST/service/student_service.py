from sqlalchemy.orm import Session

from app.REST.data.student_history_repository import (
    add_student_history,
    get_student_history_by_student_id,
)
from app.REST.data.student_repository import (
    add_student,
    delete_student,
    get_all_students,
    get_student_by_id,
    save_student,
)
from app.REST.model.student_history_orm import StudentHistoryORM
from app.REST.model.student_orm import StudentORM
from app.REST.model.student_schema import StudentCreate, StudentUpdate
from app.REST.service.student_validators import (
    validate_ects_non_negative,
    validate_ects_range,
    validate_email_forbidden_phrases,
    validate_field_of_study_exists,
    validate_student_code_alphanumeric,
    validate_student_code_length,
    validate_student_code_unique,
)


def _validate_student_full_data(db: Session, payload: StudentCreate, student_id: int = None):
    """
    Prywatna metoda pomocnicza do pełnej walidacji danych studenta (Zasada DRY).
    Konsoliduje reguły wymagane przy operacjach POST i PUT.
    """
    validate_student_code_length(payload.student_code)
    validate_student_code_alphanumeric(payload.student_code)
    validate_student_code_unique(db, payload.student_code, student_id)

    field = validate_field_of_study_exists(db, payload.field_of_study_id)

    validate_ects_non_negative(payload.ects_points)
    validate_ects_range(field, payload.ects_points)

    validate_email_forbidden_phrases(db, payload.email)

    return field


def _build_student_snapshot(student: StudentORM) -> dict:
    field = student.field_of_study
    faculty = field.faculty if field is not None else None

    return {
        "id": student.id,
        "name": student.name,
        "lastname": student.lastname,
        "student_code": student.student_code,
        "email": student.email,
        "ects_points": student.ects_points,
        "field_of_study": {
            "id": field.id if field is not None else None,
            "name": field.name if field is not None else None,
            "min_ects": field.min_ects if field is not None else None,
            "max_ects": field.max_ects if field is not None else None,
            "faculty": {
                "id": faculty.id if faculty is not None else None,
                "name": faculty.name if faculty is not None else None,
            },
        },
    }


def _save_student_history(
    db: Session,
    student_id: int | None,
    previous_state: dict,
    current_state: dict,
    action: str,
):
    history_entry = StudentHistoryORM(
        student_id=student_id,
        action=action,
        previous_state=previous_state,
        current_state=current_state,
    )
    return add_student_history(db, history_entry)


def list_students(db: Session):
    return get_all_students(db)


def get_student(db: Session, student_id: int):
    return get_student_by_id(db, student_id)


def list_student_history(db: Session, student_id: int):
    return get_student_history_by_student_id(db, student_id)


def create_student(db: Session, payload: StudentCreate):
    _validate_student_full_data(db, payload)

    student = StudentORM(
        name=payload.name,
        lastname=payload.lastname,
        student_code=payload.student_code,
        email=payload.email,
        field_of_study_id=payload.field_of_study_id,
        ects_points=payload.ects_points,
    )

    created_student = add_student(db, student)

    current_state = _build_student_snapshot(created_student)

    _save_student_history(
        db=db,
        student_id=created_student.id,
        previous_state={},
        current_state=current_state,
        action="CREATE",
    )

    return created_student


def replace_student(db: Session, student_id: int, payload: StudentCreate):
    student = get_student_by_id(db, student_id)
    if student is None:
        return None

    previous_state = _build_student_snapshot(student)

    _validate_student_full_data(db, payload, student_id)

    student.name = payload.name
    student.lastname = payload.lastname
    student.student_code = payload.student_code
    student.email = payload.email
    student.field_of_study_id = payload.field_of_study_id
    student.ects_points = payload.ects_points

    updated_student = save_student(db, student)

    current_state = _build_student_snapshot(updated_student)

    _save_student_history(
        db=db,
        student_id=updated_student.id,
        previous_state=previous_state,
        current_state=current_state,
        action="REPLACE",
    )

    return updated_student


def patch_student(db: Session, student_id: int, payload: StudentUpdate):
    student = get_student_by_id(db, student_id)
    if student is None:
        return None

    previous_state = _build_student_snapshot(student)

    if payload.student_code is not None:
        validate_student_code_length(payload.student_code)
        validate_student_code_alphanumeric(payload.student_code)
        validate_student_code_unique(db, payload.student_code, student_id)
        student.student_code = payload.student_code

    field_id_to_validate = payload.field_of_study_id or student.field_of_study_id
    field = validate_field_of_study_exists(db, field_id_to_validate)

    if payload.ects_points is not None:
        validate_ects_non_negative(payload.ects_points)
        validate_ects_range(field, payload.ects_points)
        student.ects_points = payload.ects_points

    if payload.email is not None:
        validate_email_forbidden_phrases(db, payload.email)
        student.email = payload.email

    if payload.name is not None:
        student.name = payload.name
    if payload.lastname is not None:
        student.lastname = payload.lastname
    if payload.field_of_study_id is not None:
        student.field_of_study_id = payload.field_of_study_id

    updated_student = save_student(db, student)

    current_state = _build_student_snapshot(updated_student)

    _save_student_history(
        db=db,
        student_id=updated_student.id,
        previous_state=previous_state,
        current_state=current_state,
        action="UPDATE",
    )

    return updated_student


def remove_student(db: Session, student_id: int):
    student = get_student_by_id(db, student_id)

    if student is None:
        return False

    previous_state = _build_student_snapshot(student)

    _save_student_history(
        db=db,
        student_id=student.id,
        previous_state=previous_state,
        current_state={},
        action="DELETE",
    )

    delete_student(db, student)

    return True