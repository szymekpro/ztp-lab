# app/identity/service/auth_service.py
import secrets
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.identity.data.operator_repository import (
    add_operator,
    get_operator_by_email,
    get_operator_by_id,
)
from app.identity.data.operator_session_repository import (
    add_operator_session,
    delete_session_by_id,
    delete_session_by_token,
    get_session_by_token,
    update_session_last_used,
)
from app.identity.model.operator_orm import OperatorORM
from app.identity.model.operator_session_orm import OperatorSessionORM
from app.identity.service.auth_exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
)
from app.identity.service.auth_validators import (
    validate_name,
    validate_password_strength,
)
from app.identity.service.password_hasher import hash_password, verify_password


SESSION_MAX_AGE_SECONDS = 900


def generate_session_token() -> str:
    return secrets.token_urlsafe(32)


def is_session_expired(last_used_at: datetime) -> bool:
    return datetime.now() - last_used_at > timedelta(seconds=SESSION_MAX_AGE_SECONDS)


def register_operator(
    db: Session,
    email: str,
    password: str,
    first_name: str,
    last_name: str,
) -> OperatorORM:
    existing_operator = get_operator_by_email(db, email)
    if existing_operator is not None:
        raise ConflictError("Konto z takim adresem email już istnieje.")

    validate_password_strength(password)
    validate_name(first_name, "Imię")
    validate_name(last_name, "Nazwisko")

    operator = OperatorORM(
        email=email,
        password_hash=hash_password(password),
        first_name=first_name.strip(),
        last_name=last_name.strip(),
        is_active=True,
    )

    return add_operator(db, operator)


def login_operator(db: Session, email: str, password: str) -> tuple[OperatorORM, str]:
    operator = get_operator_by_email(db, email)

    if operator is None:
        raise AuthenticationError("Niepoprawny email lub hasło.")

    if not operator.is_active:
        raise AuthorizationError("Konto operatora jest nieaktywne.")

    if not verify_password(password, operator.password_hash):
        raise AuthenticationError("Niepoprawny email lub hasło.")

    session_token = generate_session_token()

    session = OperatorSessionORM(
        operator_id=operator.id,
        session_token=session_token,
    )
    add_operator_session(db, session)

    return operator, session_token


def get_current_operator(db: Session, session_token: str) -> OperatorORM:
    session = get_session_by_token(db, session_token)
    if session is None:
        raise AuthorizationError("Brak aktywnej sesji.")

    if is_session_expired(session.last_used_at):
        delete_session_by_id(db, session.id)
        raise AuthorizationError("Sesja wygasła.")

    operator = get_operator_by_id(db, session.operator_id)
    if operator is None:
        delete_session_by_id(db, session.id)
        raise AuthorizationError("Operator przypisany do sesji nie istnieje.")

    if not operator.is_active:
        delete_session_by_id(db, session.id)
        raise AuthorizationError("Konto operatora jest nieaktywne.")

    update_session_last_used(db, session)
    return operator


def logout_operator(db: Session, session_token: str) -> bool:
    return delete_session_by_token(db, session_token)