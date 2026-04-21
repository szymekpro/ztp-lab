from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.REST.data.database import Base


class OperatorSessionORM(Base):
    __tablename__ = "operator_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    operator_id: Mapped[int] = mapped_column(Integer, ForeignKey("operators.id", ondelete="CASCADE"), nullable=False)
    session_token: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
    last_used_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)