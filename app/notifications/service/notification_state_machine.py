from app.notifications.model.notification_status import NotificationStatus


ALLOWED_TRANSITIONS = {
    NotificationStatus.PENDING: {
        NotificationStatus.SENT,
        NotificationStatus.FAILED,
        NotificationStatus.CANCELLED,
    },
    NotificationStatus.SENT: set(),
    NotificationStatus.FAILED: set(),
    NotificationStatus.CANCELLED: set(),
}


def can_transition(
    current_status: NotificationStatus,
    new_status: NotificationStatus,
) -> bool:
    return new_status in ALLOWED_TRANSITIONS.get(current_status, set())
