from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String

from app.REST.data.database import Base


class ForbiddenProductNameORM(Base):
    __tablename__ = "forbidden_product_names"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    phrase: Mapped[str] = mapped_column(String, unique=True)
