from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.cart.model.order_orm import OrderORM
from app.notifications.model.notification_channel import NotificationChannel
from app.notifications.model.notification_schema import NotificationCreate
from app.notifications.service.notification_service import create_notification


def _build_order_completed_content(order: OrderORM) -> str:
    return (
        f"Zamówienie {order.order_number} zostało zakończone. "
        f"Liczba pozycji: {order.items_count}. "
        f"Suma: {order.total_price} PLN. "
        f"Status: {order.status}."
    )


def create_order_completed_notifications(
    db: Session,
    order: OrderORM,
    operator_email: str,
    notify_email: bool,
    notify_push: bool,
) -> None:
    content = _build_order_completed_content(order)

    scheduled_at = datetime.now(timezone.utc) + timedelta(seconds=1)

    if notify_email:
        email_notification = NotificationCreate(
            content=content,
            channel=NotificationChannel.EMAIL,
            recipient=operator_email,
            scheduled_at=scheduled_at,
            timezone="UTC",
        )

        create_notification(
            db=db,
            notification_data=email_notification,
        )

    if notify_push:
        push_notification = NotificationCreate(
            content=content,
            channel=NotificationChannel.PUSH,
            recipient="test",
            scheduled_at=scheduled_at,
            timezone="UTC",
        )

        create_notification(
            db=db,
            notification_data=push_notification,
        )
