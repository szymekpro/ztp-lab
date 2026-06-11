import uuid
import pytest


def _unique_email() -> str:
    return f"basket_{uuid.uuid4().hex[:8]}@example.com"


def _register_and_login(client, email: str) -> None:
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "StrongPass1!",
            "confirm_password": "StrongPass1!",
            "first_name": "Test",
            "last_name": "Basket",
        },
    )
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "StrongPass1!"},
    )
    assert login_resp.status_code == 200


def _add_product_and_checkout(client) -> dict:
    add_resp = client.post(
        "/api/v1/cart/items",
        json={"product_id": 1, "quantity": 1},
    )
    assert add_resp.status_code == 201

    checkout_resp = client.post("/api/v1/cart/checkout")
    assert checkout_resp.status_code == 201
    return checkout_resp.json()


def _setup(client) -> dict:
    email = _unique_email()
    _register_and_login(client, email)
    return _add_product_and_checkout(client)


def test_register_and_login(client):
    email = _unique_email()

    reg_resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "StrongPass1!",
            "confirm_password": "StrongPass1!",
            "first_name": "Jan",
            "last_name": "Kowalski",
        },
    )
    assert reg_resp.status_code == 201
    data = reg_resp.json()
    assert data["email"] == email
    assert data["is_active"] is True

    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "StrongPass1!"},
    )
    assert login_resp.status_code == 200
    assert "auth_token" in login_resp.cookies


def test_add_products_to_cart(client):
    _register_and_login(client, _unique_email())

    resp = client.post(
        "/api/v1/cart/items",
        json={"product_id": 1, "quantity": 2},
    )
    assert resp.status_code == 201
    cart = resp.json()

    assert cart["items_count"] == 1
    assert cart["items"][0]["product"]["id"] == 1
    assert cart["items"][0]["quantity"] == 2
    assert float(cart["total_price"]) > 0


def test_checkout_creates_order_with_pending_status(client):
    _register_and_login(client, _unique_email())

    client.post(
        "/api/v1/cart/items",
        json={"product_id": 2, "quantity": 1},
    )

    checkout_resp = client.post("/api/v1/cart/checkout")
    assert checkout_resp.status_code == 201

    order = checkout_resp.json()
    assert order["status"] == "PENDING"
    assert order["items_count"] == 1
    assert order["order_number"].startswith("ZAM-")
    assert "id" in order


def test_complete_order_changes_status_to_completed(client):
    order = _setup(client)
    order_id = order["id"]
    idempotency_key = f"complete-{uuid.uuid4().hex}"

    resp = client.post(
        f"/api/v1/orders/{order_id}/complete",
        headers={"Idempotency-Key": idempotency_key},
    )
    assert resp.status_code == 200

    completed = resp.json()
    assert completed["id"] == order_id
    assert completed["status"] == "COMPLETED"


def test_idempotency_key_same_key_returns_200_without_reprocessing(client):
    order = _setup(client)
    order_id = order["id"]
    idempotency_key = f"complete-{uuid.uuid4().hex}"

    first_resp = client.post(
        f"/api/v1/orders/{order_id}/complete",
        headers={"Idempotency-Key": idempotency_key},
    )
    assert first_resp.status_code == 200
    assert first_resp.json()["status"] == "COMPLETED"

    second_resp = client.post(
        f"/api/v1/orders/{order_id}/complete",
        headers={"Idempotency-Key": idempotency_key},
    )
    assert second_resp.status_code == 200
    assert second_resp.json()["status"] == "COMPLETED"
    assert second_resp.json()["id"] == order_id


def test_different_idempotency_key_on_completed_order_is_blocked(client):
    order = _setup(client)
    order_id = order["id"]

    first_key = f"complete-{uuid.uuid4().hex}"
    first_resp = client.post(
        f"/api/v1/orders/{order_id}/complete",
        headers={"Idempotency-Key": first_key},
    )
    assert first_resp.status_code == 200
    assert first_resp.json()["status"] == "COMPLETED"

    different_key = f"complete-{uuid.uuid4().hex}"
    blocked_resp = client.post(
        f"/api/v1/orders/{order_id}/complete",
        headers={"Idempotency-Key": different_key},
    )
    assert blocked_resp.status_code == 400
    assert "COMPLETED" in blocked_resp.json()["detail"]


def test_complete_order_creates_email_and_push_notifications(client):
    order = _setup(client)
    order_id = order["id"]
    order_number = order["order_number"]
    idempotency_key = f"complete-{uuid.uuid4().hex}"

    complete_resp = client.post(
        f"/api/v1/orders/{order_id}/complete",
        headers={"Idempotency-Key": idempotency_key},
    )
    assert complete_resp.status_code == 200

    notifications_resp = client.get("/api/v1/notifications")
    assert notifications_resp.status_code == 200
    notifications = notifications_resp.json()

    order_notifications = [n for n in notifications if order_number in n["content"]]
    channels = {n["channel"] for n in order_notifications}

    assert "EMAIL" in channels, "Brak powiadomienia EMAIL po zakończeniu zamówienia."
    assert "PUSH" in channels, "Brak powiadomienia PUSH po zakończeniu zamówienia."


def test_idempotency_key_does_not_create_duplicate_notifications(client):
    order = _setup(client)
    order_id = order["id"]
    order_number = order["order_number"]
    idempotency_key = f"complete-{uuid.uuid4().hex}"

    client.post(
        f"/api/v1/orders/{order_id}/complete",
        headers={"Idempotency-Key": idempotency_key},
    )

    before = client.get("/api/v1/notifications").json()
    count_before = sum(1 for n in before if order_number in n["content"])

    client.post(
        f"/api/v1/orders/{order_id}/complete",
        headers={"Idempotency-Key": idempotency_key},
    )

    after = client.get("/api/v1/notifications").json()
    count_after = sum(1 for n in after if order_number in n["content"])

    assert count_after == count_before, (
        "Ponowne wywołanie z tym samym Idempotency-Key nie powinno tworzyć nowych powiadomień."
    )
