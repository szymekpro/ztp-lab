from app.notifications.model.notification_channel import NotificationChannel
from app.notifications.model.notification_orm import NotificationORM
from app.notifications.service.notification_delivery_service import (
    send_email_notification,
    send_push_notification,
)


def dispatch_notification(notification: NotificationORM) -> None:
    """
    Wybiera właściwy mechanizm wysyłki na podstawie kanału komunikacji.
    """
    channel = NotificationChannel(notification.channel)

    if channel == NotificationChannel.EMAIL:
        send_email_notification(notification)
        return

    if channel == NotificationChannel.PUSH:
        send_push_notification(notification)
        return

    raise ValueError(f"Nieobsługiwany kanał powiadomienia: {notification.channel}")
