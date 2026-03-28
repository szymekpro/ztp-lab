from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.REST.data.database import get_db
from app.notifications.model.notification_schema import (
    NotificationCreate,
    NotificationResponse,
    NotificationStatusUpdate,
)
from app.notifications.service.notification_service import (
    create_notification,
    get_notification_or_raise,
    list_notifications,
    update_notification_status,
)


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
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
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
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
