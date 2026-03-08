from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Numeric, ForeignKey

from data.database import Base


class ProductORM(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("categories.id"))
    price: Mapped[float] = mapped_column(Numeric(10, 2))
