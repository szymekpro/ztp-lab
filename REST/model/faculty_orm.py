from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String

from data.database import Base


class FacultyORM(Base):
    __tablename__ = "faculties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)