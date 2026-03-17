from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, ForeignKey

from app.REST.data.database import Base
from app.REST.model.field_of_study_orm import FieldOfStudyORM


class StudentORM(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    lastname: Mapped[str] = mapped_column(String)
    student_code: Mapped[str] = mapped_column(String, unique=True)
    email: Mapped[str] = mapped_column(String, unique=True)
    field_of_study_id: Mapped[int] = mapped_column(ForeignKey("fields_of_study.id"))
    ects_points: Mapped[int] = mapped_column(Integer)

    field_of_study = relationship("FieldOfStudyORM")