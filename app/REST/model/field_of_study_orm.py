from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, ForeignKey

from app.REST.data.database import Base
from app.REST.model.faculty_orm import FacultyORM


class FieldOfStudyORM(Base):
    __tablename__ = "fields_of_study"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    faculty_id: Mapped[int] = mapped_column(ForeignKey("faculties.id"))
    min_ects: Mapped[int] = mapped_column(Integer)
    max_ects: Mapped[int] = mapped_column(Integer)

    faculty = relationship("FacultyORM")