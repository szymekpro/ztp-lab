# service/student_validators.py
from app.REST.data.student_repository import get_student_by_student_code
from app.REST.data.field_of_study_repository import get_field_of_study_by_id
from app.REST.data.forbidden_email_phrase_repository import get_forbidden_email_phrases

class ValidationError(Exception):
    pass

class ConflictError(Exception):
    pass

class ResourceNotFoundError(Exception):
    pass

def validate_student_code_length(student_code: str):
    if not (5 <= len(student_code) <= 10):
        raise ValidationError("Numer albumu studenta musi mieć długość od 5 do 10 znaków.")

def validate_student_code_alphanumeric(student_code: str):
    if not student_code.isalnum():
        raise ValidationError("Numer albumu może zawierać wyłącznie litery i cyfry.")

def validate_student_code_unique(db, student_code: str, current_student_id=None):
    existing = get_student_by_student_code(db, student_code)
    if existing:
        if current_student_id is None or existing.id != current_student_id:
            raise ConflictError("Numer albumu już istnieje.")

def validate_field_of_study_exists(db, field_of_study_id: int):
    field = get_field_of_study_by_id(db, field_of_study_id)
    if field is None:
        raise ResourceNotFoundError("Kierunek studiów nie istnieje.")
    return field

def validate_ects_non_negative(ects_points: int):
    if ects_points < 0:
        raise ValidationError("Punkty ECTS nie mogą być ujemne.")

def validate_ects_range(field, ects_points: int):
    if ects_points < field.min_ects or ects_points > field.max_ects:
        raise ValidationError("Punkty ECTS wykraczają poza zakres dopuszczalny dla kierunku.")

def validate_email_forbidden_phrases(db, email: str):
    phrases = get_forbidden_email_phrases(db)
    email_lower = email.lower()
    for phrase in phrases:
        if phrase.lower() in email_lower:
            raise ValidationError("Email zawiera zakazaną frazę.")