import time

from sqlalchemy.orm import Session

from app.REST.data.database import SessionLocal
from app.notifications.data.notification_repository import get_ready_notifications
from app.notifications.service.notification_service import execute_notification


def process_ready_notifications(db: Session) -> int:
    """
    Pobiera wszystkie powiadomienia gotowe do realizacji i wykonuje je po kolei.
    Zwraca liczbę przetworzonych rekordów.
    """
    notifications = get_ready_notifications(db)

    for notification in notifications:
        execute_notification(db, notification.id)

    return len(notifications)


def run_worker(interval_seconds: int = 5) -> None:
    """
    Prosty worker uruchamiany w nieskończonej pętli.
    Co interval_seconds sekund pobiera rekordy gotowe do realizacji.
    """
    print(f"[WORKER] Uruchomiono worker. Interwał: {interval_seconds} s")

    while True:
        db = SessionLocal()
        try:
            processed = process_ready_notifications(db)
            if processed:
                print(f"[WORKER] Przetworzono {processed} powiadomień.")
        except Exception as exc:
            print(f"[WORKER] Wystąpił błąd: {exc}")
        finally:
            db.close()

        time.sleep(interval_seconds)


if __name__ == "__main__":
    run_worker(interval_seconds=5)
