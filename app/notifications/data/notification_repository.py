from sqlalchemy.orm import Session

from app.notifications.model.notification_orm import NotificationORM


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
