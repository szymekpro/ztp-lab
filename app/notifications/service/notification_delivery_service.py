import requests
import smtplib
from email.message import EmailMessage
from app.notifications.model.notification_orm import NotificationORM

def send_email_notification(notification: NotificationORM) -> None:
    msg = EmailMessage()
    msg.set_content(notification.content)
    msg["Subject"] = "Notification"
    msg["From"] = "noreply@ztp.local"
    msg["To"] = notification.recipient

    with smtplib.SMTP("localhost", 1025) as server:
        server.send_message(msg)

def send_push_notification(notification: NotificationORM) -> None:
    response = requests.post(
        f"http://localhost:8088/{notification.recipient}",
        data=notification.content.encode("utf-8"),
        timeout=5,
    )
    response.raise_for_status()