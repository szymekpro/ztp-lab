from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.REST.data.database import Base


class StudentHistoryORM(Base):
    __tablename__ = "student_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True  
    )
    action: Mapped[str] = mapped_column(String, nullable=False)
    previous_state: Mapped[dict] = mapped_column(JSON, nullable=False)
    current_state: Mapped[dict] = mapped_column(JSON, nullable=False)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now()
    )