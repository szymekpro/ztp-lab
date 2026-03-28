from sqlalchemy.orm import Session

from app.notifications.data.notification_repository import (
    add_notification,
    get_all_notifications,
    get_notification_by_id,
    save_notification,
)
from app.notifications.model.notification_orm import NotificationORM
from app.notifications.model.notification_schema import NotificationCreate
from app.notifications.model.notification_status import NotificationStatus
from app.notifications.service.notification_state_machine import can_transition
from app.notifications.service.notification_validators import (
    convert_to_utc,
    validate_content,
    validate_recipient,
    validate_scheduled_at,
    validate_timezone,
)


def create_notification(db: Session, notification_data: NotificationCreate) -> NotificationORM:
    validate_content(notification_data.content)
    validate_recipient(notification_data.recipient)
    validate_timezone(notification_data.timezone)
    validate_scheduled_at(notification_data.scheduled_at, notification_data.timezone)

    scheduled_at_utc = convert_to_utc(
        notification_data.scheduled_at,
        notification_data.timezone,
    )

    notification = NotificationORM(
        content=notification_data.content,
        channel=notification_data.channel.value,
        recipient=notification_data.recipient,
        scheduled_at=scheduled_at_utc,
        timezone=notification_data.timezone,
        status=NotificationStatus.PENDING.value,
    )

    return add_notification(db, notification)


def list_notifications(db: Session) -> list[NotificationORM]:
    return get_all_notifications(db)


def get_notification_or_raise(db: Session, notification_id: int) -> NotificationORM:
    notification = get_notification_by_id(db, notification_id)

    if notification is None:
        raise LookupError("Powiadomienie nie zostało znalezione.")

    return notification


def update_notification_status(
    db: Session,
    notification_id: int,
    new_status: NotificationStatus,
) -> NotificationORM:
    notification = get_notification_or_raise(db, notification_id)
    current_status = NotificationStatus(notification.status)

    if not can_transition(current_status, new_status):
        raise ValueError(
            f"Przejście ze statusu {current_status.value} do {new_status.value} jest niedozwolone."
        )

    notification.status = new_status.value
    return save_notification(db, notification)