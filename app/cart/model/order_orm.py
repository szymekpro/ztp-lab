from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.REST.data.database import Base


class OrderORM(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    operator_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("operators.id", ondelete="CASCADE"),
        nullable=False,
    )
    order_number: Mapped[str] = mapped_column(
        String,
        nullable=False,
        unique=True,
    )
    status: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="PENDING",
    )
    items_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_price: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=0,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now,
    )

    items = relationship(
        "OrderItemORM",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
