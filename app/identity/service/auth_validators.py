import re

from app.identity.service.auth_exceptions import ValidationError


SPECIAL_CHARACTER_PATTERN = re.compile(r"[!@#$%^&*()_\-+=\[{\]};:'\",<.>/?\\|`~]")
UPPERCASE_PATTERN = re.compile(r"[A-Z]")
DIGIT_PATTERN = re.compile(r"\d")


def validate_password_strength(password: str):
    if len(password) < 8:
        raise ValidationError("Hasło musi mieć co najmniej 8 znaków.")

    if UPPERCASE_PATTERN.search(password) is None:
        raise ValidationError("Hasło musi zawierać co najmniej jedną wielką literę.")

    if DIGIT_PATTERN.search(password) is None:
        raise ValidationError("Hasło musi zawierać co najmniej jedną cyfrę.")

    if SPECIAL_CHARACTER_PATTERN.search(password) is None:
        raise ValidationError("Hasło musi zawierać co najmniej jeden znak specjalny.")


def validate_name(name: str, field_name: str):
    stripped = name.strip()

    if len(stripped) < 3:
        raise ValidationError(f"{field_name} musi mieć co najmniej 2 znaki.")

    if len(stripped) > 50:
        raise ValidationError(f"{field_name} nie może być dłuższe niż 50 znaków.")