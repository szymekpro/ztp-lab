from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from service.student_service import list_students
from data.database import get_db
from model.student_schema import Student

router = APIRouter()

@router.get("/students", response_model=list[Student]) #list[StudentORM] -> list[Student] -> json
def get_students(db: Session = Depends(get_db)):
    return list_students(db)