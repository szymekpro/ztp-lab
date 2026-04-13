from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.notifications.model.notification_orm import NotificationORM
from app.notifications.model.notification_status import NotificationStatus
from app.notifications.service.notification_validators import convert_to_utc

def build_push_notification_payload() -> dict:
    scheduled_local = datetime.now(ZoneInfo("Europe/Warsaw")) + timedelta(minutes=10)

    return {
        "content": "Test PUSH notification",
        "channel": "PUSH",
        "recipient": "test",
        "scheduled_at": scheduled_local.replace(tzinfo=None).isoformat(timespec="seconds"),
        "timezone": "Europe/Warsaw",
    }


def build_email_notification_payload() -> dict:
    scheduled_local = datetime.now(ZoneInfo("Europe/Warsaw")) + timedelta(minutes=10)

    return {
        "content": "Test EMAIL notification",
        "channel": "EMAIL",
        "recipient": "test@example.com",
        "scheduled_at": scheduled_local.replace(tzinfo=None).isoformat(timespec="seconds"),
        "timezone": "Europe/Warsaw",
    }


def test_get_notifications_returns_200_and_list(client):
    response = client.get("/api/v1/notifications")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_post_push_notification_creates_record_and_converts_time_to_utc(client):
    payload = build_push_notification_payload()

    create_response = client.post("/api/v1/notifications", json=payload)

    assert create_response.status_code == 201
    created = create_response.json()

    assert created["content"] == payload["content"]
    assert created["channel"] == payload["channel"]
    assert created["recipient"] == "test"
    assert created["timezone"] == payload["timezone"]
    assert created["status"] == "PENDING"
    assert "id" in created
    assert "created_at" in created

    expected_utc = convert_to_utc(
        datetime.fromisoformat(payload["scheduled_at"]),
        payload["timezone"],
    )

    assert created["scheduled_at"] == expected_utc.isoformat().replace("+00:00", "Z")

    get_response = client.get("/api/v1/notifications")
    assert get_response.status_code == 200

    notifications = get_response.json()
    assert any(n["id"] == created["id"] for n in notifications)


def test_post_email_notification_creates_record_and_is_visible_on_get(client):
    payload = build_email_notification_payload()

    create_response = client.post("/api/v1/notifications", json=payload)

    assert create_response.status_code == 201
    created = create_response.json()

    assert created["content"] == payload["content"]
    assert created["channel"] == payload["channel"]
    assert created["recipient"] == payload["recipient"]
    assert created["timezone"] == payload["timezone"]
    assert created["status"] == "PENDING"

    get_response = client.get(f"/api/v1/notifications/{created['id']}")
    assert get_response.status_code == 200

    fetched = get_response.json()
    assert fetched["id"] == created["id"]
    assert fetched["content"] == payload["content"]
    assert fetched["channel"] == payload["channel"]
    assert fetched["recipient"] == payload["recipient"]
    assert fetched["status"] == "PENDING"


def test_send_now_push_notification_changes_status_to_sent(client):
    payload = build_push_notification_payload()

    create_response = client.post("/api/v1/notifications", json=payload)
    assert create_response.status_code == 201

    notification_id = create_response.json()["id"]

    send_response = client.post(f"/api/v1/notifications/{notification_id}/send-now")
    assert send_response.status_code == 200

    sent = send_response.json()
    assert sent["id"] == notification_id
    assert sent["channel"] == "PUSH"
    assert sent["recipient"] == "test"
    assert sent["status"] == "SENT"

    get_response = client.get(f"/api/v1/notifications/{notification_id}")
    assert get_response.status_code == 200
    fetched = get_response.json()
    assert fetched["status"] == "SENT"


def test_send_now_email_notification_changes_status_to_sent(client):
    payload = build_email_notification_payload()

    create_response = client.post("/api/v1/notifications", json=payload)
    assert create_response.status_code == 201

    notification_id = create_response.json()["id"]

    send_response = client.post(f"/api/v1/notifications/{notification_id}/send-now")
    assert send_response.status_code == 200

    sent = send_response.json()
    assert sent["id"] == notification_id
    assert sent["channel"] == "EMAIL"
    assert sent["recipient"] == payload["recipient"]
    assert sent["status"] == "SENT"

    get_response = client.get(f"/api/v1/notifications/{notification_id}")
    assert get_response.status_code == 200
    fetched = get_response.json()
    assert fetched["status"] == "SENT"


def test_post_notification_rejects_past_scheduled_at(client):
    payload = {
        "content": "Past notification",
        "channel": "PUSH",
        "recipient": "test",
        "scheduled_at": (datetime.now() - timedelta(minutes=5)).isoformat(timespec="seconds"),
        "timezone": "Europe/Warsaw",
    }

    response = client.post("/api/v1/notifications", json=payload)

    assert response.status_code == 422
    body = response.json()
    assert body["detail"] == "Planowana data wysyłki musi wskazywać przyszły moment."


def test_post_notification_rejects_invalid_timezone(client):
    payload = {
        "content": "Invalid timezone",
        "channel": "PUSH",
        "recipient": "test",
        "scheduled_at": (datetime.now() + timedelta(minutes=10)).isoformat(timespec="seconds"),
        "timezone": "Mars/Phobos",
    }

    response = client.post("/api/v1/notifications", json=payload)

    assert response.status_code == 422
    body = response.json()
    assert body["detail"] == "Podana strefa czasowa jest nieprawidłowa."


def test_post_notification_rejects_empty_recipient(client):
    payload = {
        "content": "Missing recipient",
        "channel": "EMAIL",
        "recipient": "   ",
        "scheduled_at": (datetime.now() + timedelta(minutes=10)).isoformat(timespec="seconds"),
        "timezone": "Europe/Warsaw",
    }

    response = client.post("/api/v1/notifications", json=payload)

    assert response.status_code == 422
    body = response.json()
    assert body["detail"] == "Odbiorca nie może być pusty."


def test_send_now_for_already_sent_notification_returns_422(client):
    payload = build_push_notification_payload()

    create_response = client.post("/api/v1/notifications", json=payload)
    assert create_response.status_code == 201

    notification_id = create_response.json()["id"]

    first_send_response = client.post(f"/api/v1/notifications/{notification_id}/send-now")
    assert first_send_response.status_code == 200
    assert first_send_response.json()["status"] == "SENT"

    second_send_response = client.post(f"/api/v1/notifications/{notification_id}/send-now")
    assert second_send_response.status_code == 422

    body = second_send_response.json()
    assert body["detail"] == "Wykonać można wyłącznie powiadomienie w statusie PENDING."


def test_process_ready_notifications_processes_only_due_records(client, db_session):
    now_utc = datetime.now(ZoneInfo("UTC"))

    ready_notification = NotificationORM(
        content="Ready PUSH notification",
        channel="PUSH",
        recipient="test",
        scheduled_at=now_utc - timedelta(minutes=1),
        timezone="Europe/Warsaw",
        status=NotificationStatus.PENDING.value,
    )

    future_notification = NotificationORM(
        content="Future PUSH notification",
        channel="PUSH",
        recipient="test",
        scheduled_at=now_utc + timedelta(minutes=10),
        timezone="Europe/Warsaw",
        status=NotificationStatus.PENDING.value,
    )

    db_session.add_all([ready_notification, future_notification])
    db_session.commit()
    db_session.refresh(ready_notification)
    db_session.refresh(future_notification)

    process_response = client.post("/api/v1/notifications/process-ready")

    assert process_response.status_code == 200
    assert process_response.json() == {"processed_count": 1}

    ready_after = client.get(f"/api/v1/notifications/{ready_notification.id}")
    assert ready_after.status_code == 200
    assert ready_after.json()["status"] == "SENT"

    future_after = client.get(f"/api/v1/notifications/{future_notification.id}")
    assert future_after.status_code == 200
    assert future_after.json()["status"] == "PENDING"