from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.REST.data.database import get_db
from app.REST.model.student_schema import (
    Student,
    StudentCreate,
    StudentHistoryEntry,
    StudentUpdate,
)
from app.REST.service.student_service import (
    create_student,
    get_student,
    list_student_history,
    list_students,
    patch_student,
    remove_student,
    replace_student,
)
from app.REST.service.student_validators import (
    ConflictError,
    ResourceNotFoundError,
    ValidationError,
)

# Inicjalizacja routera FastAPI
router = APIRouter()


@router.get("/students", response_model=list[Student])
def get_students(db: Session = Depends(get_db)):
    # Pobranie listy wszystkich studentów - domyślnie zwraca status 200 OK
    return list_students(db)


@router.get("/students/{id}", response_model=Student)
def get_student_by_id_endpoint(id: int, db: Session = Depends(get_db)):
    # Próba pobrania konkretnego studenta
    student = get_student(db, id)

    # Jeśli serwis nie zwrócił obiektu, podnosimy błąd 404 Not Found
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")

    return student


@router.get("/students/{id}/history", response_model=list[StudentHistoryEntry])
def get_student_history_endpoint(id: int, db: Session = Depends(get_db)):
    # Pobranie historii zmian konkretnego studenta
    history = list_student_history(db, id)

    # Jeżeli student nie istnieje, zwracamy 404
    if history is None:
        raise HTTPException(status_code=404, detail="Student not found")

    return history


@router.post("/students", response_model=Student, status_code=201)
def post_student(payload: StudentCreate, db: Session = Depends(get_db)):
    # Próba utworzenia nowego zasobu z obsługą wyjątków domenowych
    try:
        # Sukces zwraca status 201 Created
        return create_student(db, payload)

    except ValidationError as e:
        # Błędy reguł biznesowych mapujemy na status 422
        raise HTTPException(status_code=422, detail=str(e))

    except ConflictError as e:
        # Naruszenie unikalności (np. numeru albumu) mapujemy na 409
        raise HTTPException(status_code=409, detail=str(e))

    except ResourceNotFoundError as e:
        # Brak powiązanych zasobów (np. kierunku) mapujemy na 400
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/students/{id}", response_model=Student)
def put_student(id: int, payload: StudentCreate, db: Session = Depends(get_db)):
    # Pełna aktualizacja zasobu (zastąpienie)
    try:
        student = replace_student(db, id, payload)

        # Pierwszym krokiem jest zawsze sprawdzenie, czy główny zasób istnieje
        if student is None:
            raise HTTPException(status_code=404, detail="Student not found")

        return student

    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/students/{id}", response_model=Student)
def patch_student_endpoint(id: int, payload: StudentUpdate, db: Session = Depends(get_db)):
    # Częściowa aktualizacja zasobu
    try:
        student = patch_student(db, id, payload)

        # Podobnie jak w PUT, brak zasobu skutkuje błędem 404
        if student is None:
            raise HTTPException(status_code=404, detail="Student not found")

        return student

    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/students/{id}", status_code=204)
def delete_student_endpoint(id: int, db: Session = Depends(get_db)):
    # Próba usunięcia zasobu
    # Serwis zwraca wartość logiczną informującą o sukcesie operacji
    if not remove_student(db, id):
        # Jeśli zasób nie istniał, informujemy o tym klienta (404)
        raise HTTPException(status_code=404, detail="Student not found")

    # Przy sukcesie zwracamy status 204 No Content bez treści w body odpowiedzi
    return Response(status_code=204)