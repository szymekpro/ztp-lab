from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.notifications.model.notification_orm import NotificationORM
from app.notifications.model.notification_status import NotificationStatus


def add_notification(db: Session, notification: NotificationORM) -> NotificationORM:
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def get_all_notifications(db: Session) -> list[NotificationORM]:
    return db.query(NotificationORM).order_by(NotificationORM.id.asc()).all()


def get_notification_by_id(db: Session, notification_id: int) -> NotificationORM | None:
    return (
        db.query(NotificationORM)
        .filter(NotificationORM.id == notification_id)
        .first()
    )


def save_notification(db: Session, notification: NotificationORM) -> NotificationORM:
    db.commit()
    db.refresh(notification)
    return notification


def get_ready_notifications(db: Session) -> list[NotificationORM]:
    now_utc = datetime.now(timezone.utc)

    return (
        db.query(NotificationORM)
        .filter(NotificationORM.status == NotificationStatus.PENDING.value)
        .filter(NotificationORM.scheduled_at <= now_utc)
        .order_by(NotificationORM.scheduled_at.asc())
        .all()
    )
