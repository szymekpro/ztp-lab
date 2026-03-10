# service/student_service.py
from sqlalchemy.orm import Session
from data.student_repository import (
    get_all_students,
    get_student_by_id,
    add_student,
    save_student,
    delete_student,
)
from model.student_orm import StudentORM
from model.student_schema import StudentCreate, StudentUpdate
from service.student_validators import (
    validate_student_code_length,
    validate_student_code_alphanumeric,
    validate_student_code_unique,
    validate_field_of_study_exists,
    validate_ects_non_negative,
    validate_ects_range,
    validate_email_forbidden_phrases,
)

def _validate_student_full_data(db: Session, payload: StudentCreate, student_id: int = None):
    """
    Prywatna metoda pomocnicza do pełnej walidacji danych studenta (Zasada DRY).
    Konsoliduje reguły wymagane przy operacjach POST i PUT.
    """
    # Walidacja tożsamości (Numer albumu: długość, znaki, unikalność)
    validate_student_code_length(payload.student_code)
    validate_student_code_alphanumeric(payload.student_code)
    validate_student_code_unique(db, payload.student_code, student_id)
    
    # Walidacja powiązań (Sprawdzenie czy kierunek studiów istnieje w bazie)
    field = validate_field_of_study_exists(db, payload.field_of_study_id)
    
    # Walidacja punktów ECTS (Nieujemność oraz zgodność z zakresem kierunku)
    validate_ects_non_negative(payload.ects_points)
    validate_ects_range(field, payload.ects_points)
    
    # Walidacja polityki systemu (Sprawdzenie e-mail pod kątem zakazanych fraz)
    validate_email_forbidden_phrases(db, payload.email)
    
    return field

def list_students(db: Session):
    # Pobranie listy wszystkich studentów z repozytorium
    return get_all_students(db)

def get_student(db: Session, student_id: int):
    # Pobranie konkretnego studenta po ID (Web Layer obsłuży None jako 404)
    return get_student_by_id(db, student_id)

def create_student(db: Session, payload: StudentCreate):
    # Wykonanie pełnego zestawu walidacji przed utworzeniem
    _validate_student_full_data(db, payload)

    # Tworzenie obiektu ORM na podstawie przesłanych danych
    student = StudentORM(
        name=payload.name,
        lastname=payload.lastname,
        student_code=payload.student_code,
        email=payload.email,
        field_of_study_id=payload.field_of_study_id,
        ects_points=payload.ects_points,
    )

    # Dodanie studenta do bazy danych przez warstwę repozytorium
    return add_student(db, student)

def replace_student(db: Session, student_id: int, payload: StudentCreate):
    # Sprawdzenie, czy zasób do aktualizacji (PUT) w ogóle istnieje
    student = get_student_by_id(db, student_id)
    if student is None:
        return None  # Sygnał dla Routes do rzucenia 404

    # Pełna walidacja nowych danych (przekazujemy student_id, by zignorować autokolizję kodu)
    _validate_student_full_data(db, payload, student_id)

    # Nadpisanie wszystkich pól istniejącego obiektu ORM
    student.name = payload.name
    student.lastname = payload.lastname
    student.student_code = payload.student_code
    student.email = payload.email
    student.field_of_study_id = payload.field_of_study_id
    student.ects_points = payload.ects_points

    # Trwałe zapisanie zmian w bazie danych
    return save_student(db, student)

def patch_student(db: Session, student_id: int, payload: StudentUpdate):
    # Weryfikacja istnienia głównego zasobu do częściowej aktualizacji
    student = get_student_by_id(db, student_id)
    if student is None:
        return None

    # Warunkowa walidacja numeru albumu (tylko jeśli klient przesłał to pole)
    if payload.student_code is not None:
        validate_student_code_length(payload.student_code)
        validate_student_code_alphanumeric(payload.student_code)
        validate_student_code_unique(db, payload.student_code, student_id)
        student.student_code = payload.student_code

    # Inteligentny wybór kierunku do walidacji zakresu punktów ECTS
    # Jeśli klient zmienia kierunek - bierzemy nowy, jeśli nie - bierzemy obecny z bazy
    field_id_to_validate = payload.field_of_study_id or student.field_of_study_id
    field = validate_field_of_study_exists(db, field_id_to_validate)
    
    # Walidacja ECTS (zawsze sprawdzana względem poprawnego kontekstu kierunku)
    if payload.ects_points is not None:
        validate_ects_non_negative(payload.ects_points)
        validate_ects_range(field, payload.ects_points)
        student.ects_points = payload.ects_points

    # Sprawdzenie polityki email i aktualizacja pozostałych pól tekstowych
    if payload.email is not None:
        validate_email_forbidden_phrases(db, payload.email)
        student.email = payload.email

    if payload.name is not None:
        student.name = payload.name
    if payload.lastname is not None:
        student.lastname = payload.lastname
    if payload.field_of_study_id is not None:
        student.field_of_study_id = payload.field_of_study_id

    # Zapisanie częściowych zmian
    return save_student(db, student)

def remove_student(db: Session, student_id: int):
    # Sprawdzenie, czy student do usunięcia istnieje w bazie
    student = get_student_by_id(db, student_id)

    if student is None:
        # Sygnał dla warstwy Web: nie można usunąć czegoś, czego nie ma
        return False

    # Wywołanie fizycznego usunięcia rekordu w warstwie danych
    delete_student(db, student)

    # Zwrócenie sukcesu operacji (Web Layer odpowie statusem 204)
    return True