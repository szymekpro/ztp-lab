from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.REST.data.database import get_db
from app.notifications.data.notification_repository import (
    count_notifications_by_status,
    count_notifications_by_status_and_channel,
)
from app.notifications.model.notification_channel import NotificationChannel
from app.notifications.model.notification_schema import (
    NotificationCreate,
    NotificationResponse,
    NotificationStatusUpdate,
)
from app.notifications.model.notification_status import NotificationStatus
from app.notifications.service.notification_service import (
    cancel_notification,
    create_notification,
    execute_notification,
    get_notification_or_raise,
    list_notifications,
    update_notification_status,
)
from app.notifications.service.notification_worker import process_ready_notifications

router = APIRouter(tags=["Notifications"])


@router.post(
    "/notifications",
    response_model=NotificationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_notification_endpoint(
    notification: NotificationCreate,
    db: Session = Depends(get_db),
):
    try:
        return create_notification(db, notification)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc


@router.get(
    "/notifications",
    response_model=list[NotificationResponse],
    status_code=status.HTTP_200_OK,
)
def get_notifications_endpoint(db: Session = Depends(get_db)):
    return list_notifications(db)


@router.get(
    "/notifications/{notification_id}",
    response_model=NotificationResponse,
    status_code=status.HTTP_200_OK,
)
def get_notification_endpoint(notification_id: int, db: Session = Depends(get_db)):
    try:
        return get_notification_or_raise(db, notification_id)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.patch(
    "/notifications/{notification_id}/status",
    response_model=NotificationResponse,
    status_code=status.HTTP_200_OK,
)
def update_notification_status_endpoint(
    notification_id: int,
    payload: NotificationStatusUpdate,
    db: Session = Depends(get_db),
):
    try:
        return update_notification_status(db, notification_id, payload.status)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc


@router.post(
    "/notifications/{notification_id}/send-now",
    response_model=NotificationResponse,
    status_code=status.HTTP_200_OK,
)
def send_notification_now_endpoint(
    notification_id: int,
    db: Session = Depends(get_db),
):
    try:
        return execute_notification(db, notification_id)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc


@router.post(
    "/notifications/process-ready",
    status_code=status.HTTP_200_OK,
)
def process_ready_notifications_endpoint(db: Session = Depends(get_db)):
    processed = process_ready_notifications(db)
    return {"processed_count": processed}


@router.patch(
    "/notifications/{notification_id}/cancel",
    status_code=status.HTTP_200_OK,
)
def cancel_notification_endpoint(
    notification_id: int,
    db: Session = Depends(get_db),
):
    try:
        return cancel_notification(db, notification_id)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc


@router.get(
    "/metrics",
    status_code=status.HTTP_200_OK,
)
def metrics_endpoint(db: Session = Depends(get_db)):
    sent = count_notifications_by_status(db, NotificationStatus.SENT.value)
    failed = count_notifications_by_status(db, NotificationStatus.FAILED.value)
    pending = count_notifications_by_status(db, NotificationStatus.PENDING.value)
    cancelled = count_notifications_by_status(db, NotificationStatus.CANCELLED.value)

    metrics_text = (
        "# HELP notifications_sent_total Number of sent notifications\n"
        "# TYPE notifications_sent_total gauge\n"
        f"notifications_sent_total {sent}\n"
        "# HELP notifications_failed_total Number of failed notifications\n"
        "# TYPE notifications_failed_total gauge\n"
        f"notifications_failed_total {failed}\n"
        "# HELP notifications_pending_total Number of pending notifications\n"
        "# TYPE notifications_pending_total gauge\n"
        f"notifications_pending_total {pending}\n"
        "# HELP notifications_cancelled_total Number of cancelled notifications\n"
        "# TYPE notifications_cancelled_total gauge\n"
        f"notifications_cancelled_total {cancelled}\n"
        "# HELP notifications_by_channel Number of notifications by status and channel\n"
        "# TYPE notifications_by_channel gauge\n"
    )

    for status_value in NotificationStatus:
        for channel_value in NotificationChannel:
            value = count_notifications_by_status_and_channel(
                db,
                status_value.value,
                channel_value.value,
            )
            metrics_text += (
                f'notifications_by_channel{{status="{status_value.value}",channel="{channel_value.value}"}} {value}\n'
            )

    return PlainTextResponse(metrics_text)