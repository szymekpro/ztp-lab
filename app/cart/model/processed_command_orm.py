from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.REST.data.database import Base


class ProcessedCommandORM(Base):
    __tablename__ = "processed_commands"

    __table_args__ = (
        UniqueConstraint(
            "command_name",
            "idempotency_key",
            name="uq_processed_command_key",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    command_name: Mapped[str] = mapped_column(String, nullable=False)

    idempotency_key: Mapped[str] = mapped_column(String, nullable=False)

    operator_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("operators.id", ondelete="CASCADE"),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now,
    )
