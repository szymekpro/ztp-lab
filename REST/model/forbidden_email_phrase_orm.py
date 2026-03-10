from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String

from data.database import Base


class ForbiddenEmailPhraseORM(Base):
    __tablename__ = "forbidden_email_phrases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    phrase: Mapped[str] = mapped_column(String, unique=True)