def build_register_payload(email: str) -> dict:
    return {
        "email": email,
        "password": "StrongPass1!",
        "confirm_password": "StrongPass1!",
        "full_name": "Jan Kowalski",
    }


def build_login_payload(email: str) -> dict:
    return {
        "email": email,
        "password": "StrongPass1!",
    }


def test_register_returns_201_and_created_operator(client):
    payload = build_register_payload("operator1@example.com")

    response = client.post("/auth/register", json=payload)

    assert response.status_code == 201
    data = response.json()

    assert data["email"] == payload["email"]
    assert data["full_name"] == payload["full_name"]
    assert data["is_active"] is True
    assert "id" in data


def test_register_rejects_weak_password(client):
    payload = {
        "email": "weak@example.com",
        "password": "weakpass",
        "confirm_password": "weakpass",
        "full_name": "Jan Kowalski",
    }

    response = client.post("/auth/register", json=payload)

    assert response.status_code == 422
    assert response.json()["detail"] == "Hasło musi zawierać co najmniej jedną wielką literę."


def test_register_rejects_when_passwords_do_not_match(client):
    payload = {
        "email": "mismatch@example.com",
        "password": "StrongPass1!",
        "confirm_password": "DifferentPass1!",
        "full_name": "Jan Kowalski",
    }

    response = client.post("/auth/register", json=payload)

    assert response.status_code == 422


def test_login_sets_cookie_and_returns_operator(client):
    register_payload = build_register_payload("operator2@example.com")
    client.post("/auth/register", json=register_payload)

    login_payload = build_login_payload("operator2@example.com")
    response = client.post("/auth/login", json=login_payload)

    assert response.status_code == 200
    assert response.cookies.get("auth_token") is not None

    data = response.json()
    assert data["operator"]["email"] == "operator2@example.com"


def test_me_returns_current_operator_when_cookie_exists(client):
    register_payload = build_register_payload("operator3@example.com")
    client.post("/auth/register", json=register_payload)

    login_payload = build_login_payload("operator3@example.com")
    login_response = client.post("/auth/login", json=login_payload)

    auth_token = login_response.cookies.get("auth_token")

    response = client.get("/auth/me", cookies={"auth_token": auth_token})

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "operator3@example.com"


def test_logout_clears_cookie_and_invalidates_session(client):
    register_payload = build_register_payload("operator4@example.com")
    client.post("/auth/register", json=register_payload)

    login_payload = build_login_payload("operator4@example.com")
    login_response = client.post("/auth/login", json=login_payload)

    auth_token = login_response.cookies.get("auth_token")

    logout_response = client.post("/auth/logout", cookies={"auth_token": auth_token})
    assert logout_response.status_code == 204

    me_response = client.get("/auth/me", cookies={"auth_token": auth_token})
    assert me_response.status_code == 401
    assert me_response.json()["detail"] == "Brak aktywnej sesji."