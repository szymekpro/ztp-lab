from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Numeric

from data.database import Base


class CategoryORM(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    min_price: Mapped[float] = mapped_column(Numeric(10, 2))
    max_price: Mapped[float] = mapped_column(Numeric(10, 2))
