from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String

from data.database import Base


class StudentORM(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    lastname: Mapped[str] = mapped_column(String)