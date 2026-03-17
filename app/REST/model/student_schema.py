import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr


class Faculty(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class FieldOfStudy(BaseModel):
    id: int
    name: str
    min_ects: int
    max_ects: int
    faculty: Faculty

    model_config = ConfigDict(from_attributes=True)


class StudentCreate(BaseModel):
    name: str
    lastname: str
    student_code: str
    email: EmailStr
    field_of_study_id: int
    ects_points: int


class StudentUpdate(BaseModel):
    name: str | None = None
    lastname: str | None = None
    student_code: str | None = None
    email: EmailStr | None = None
    field_of_study_id: int | None = None
    ects_points: int | None = None


class Student(BaseModel):
    id: int
    name: str
    lastname: str
    student_code: str
    email: EmailStr
    ects_points: int
    field_of_study: FieldOfStudy

    model_config = ConfigDict(from_attributes=True)


class StudentHistoryEntry(BaseModel):
    id: int
    student_id: int
    action: str
    previous_state: dict[str, Any]
    current_state: dict[str, Any]
    changed_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)