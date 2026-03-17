import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event

from main import app
from app.REST.data.database import engine, get_db, SessionLocal


@pytest.fixture(scope="function")
def db_session():
    """
    Przygotowuje sesję bazy danych dla testu.
    Każdy test działa w jednej transakcji, która na końcu zostaje cofnięta.
    Dzięki temu testy nie zostawiają danych w bazie.
    """
    connection = engine.connect()
    outer_transaction = connection.begin()
    session = SessionLocal(bind=connection)
    nested_transaction = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(sess, transaction):
        nonlocal nested_transaction

        if not nested_transaction.is_active:
            nested_transaction = connection.begin_nested()

    try:
        yield session

    finally:
        session.close()
        outer_transaction.rollback()
        connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    """
    Nadpisuje zależność get_db tak, aby endpointy FastAPI używały sesji testowej.
    Dzięki temu również wewnętrzne commit() wykonywane przez repozytorium
    pozostają zamknięte w transakcji testowej i zostaną cofnięte po teście.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def unique_student_code() -> str:
    """
    Generuje unikalny student_code zgodny z walidacją długości 5-10 znaków.
    Nie używamy już prefiksu do późniejszego czyszczenia danych,
    ponieważ dane są cofane rollbackiem.
    """
    return uuid.uuid4().hex[:10].upper()


@pytest.fixture
def unique_product_name() -> str:
    """Generuje unikalną nazwę produktu zgodną z walidacją (3-20, alnum)."""
    return f"PR{uuid.uuid4().hex[:8]}".upper()