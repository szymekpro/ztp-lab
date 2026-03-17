BASE_URL = "api/v1/student"

def build_student_payload(student_code: str) -> dict:
    return {
        "name": "Test",
        "lastname": "Student",
        "student_code": student_code,
        "email": f"{student_code.lower()}@student.edu.pl",
        "field_of_study_id": 1,
        "ects_points": 45,
    }


def test_get_students_returns_200_and_non_empty_list(client):
    response = client.get(f"{BASE_URL}/students")

    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

    first = data[0]
    assert "id" in first
    assert "name" in first
    assert "lastname" in first
    assert "student_code" in first
    assert "email" in first
    assert "ects_points" in first
    assert "field_of_study" in first


def test_post_students_creates_student_and_history_entry(client, unique_student_code):
    payload = build_student_payload(unique_student_code)

    create_response = client.post(f"{BASE_URL}/students", json=payload)

    assert create_response.status_code == 201
    created = create_response.json()

    assert created["name"] == payload["name"]
    assert created["lastname"] == payload["lastname"]
    assert created["student_code"] == payload["student_code"]
    assert created["email"] == payload["email"]
    assert created["ects_points"] == payload["ects_points"]
    assert created["field_of_study"]["id"] == payload["field_of_study_id"]

    student_id = created["id"]

    history_response = client.get(f"{BASE_URL}/students/{student_id}/history")
    assert history_response.status_code == 200

    history = history_response.json()
    assert isinstance(history, list)
    assert len(history) >= 1

    latest_entry = history[0]
    assert latest_entry["student_id"] == student_id
    assert latest_entry["action"] == "CREATE"
    assert latest_entry["previous_state"] == {}
    assert latest_entry["current_state"]["student_code"] == payload["student_code"]
    assert latest_entry["current_state"]["email"] == payload["email"]


def test_patch_students_updates_selected_fields_and_saves_history(client, unique_student_code):
    create_payload = build_student_payload(unique_student_code)
    create_response = client.post(f"{BASE_URL}/students", json=create_payload)
    assert create_response.status_code == 201

    created_student = create_response.json()
    student_id = created_student["id"]

    patch_payload = {
        "email": f"updated.{unique_student_code.lower()}@student.edu.pl",
        "ects_points": 50,
    }

    patch_response = client.patch(f"{BASE_URL}/students/{student_id}", json=patch_payload)

    assert patch_response.status_code == 200
    updated = patch_response.json()

    assert updated["id"] == student_id
    assert updated["student_code"] == create_payload["student_code"]
    assert updated["email"] == patch_payload["email"]
    assert updated["ects_points"] == patch_payload["ects_points"]

    history_response = client.get(f"{BASE_URL}/students/{student_id}/history")
    assert history_response.status_code == 200

    history = history_response.json()
    assert len(history) >= 2

    latest_entry = history[0]
    create_entry = history[1]

    assert latest_entry["action"] == "UPDATE"
    assert latest_entry["previous_state"]["email"] == create_payload["email"]
    assert latest_entry["current_state"]["email"] == patch_payload["email"]
    assert latest_entry["previous_state"]["ects_points"] == create_payload["ects_points"]
    assert latest_entry["current_state"]["ects_points"] == patch_payload["ects_points"]

    assert create_entry["action"] == "CREATE"


def test_post_students_rejects_forbidden_email_phrase(client, unique_student_code):
    payload = build_student_payload(unique_student_code)
    payload["email"] = f"root.{unique_student_code.lower()}@student.edu.pl"

    response = client.post(f"{BASE_URL}/students", json=payload)

    assert response.status_code == 422
    body = response.json()
    assert body["detail"] == "Email zawiera zakazaną frazę."


def test_post_students_rejects_student_code_with_invalid_length(client):
    payload = {
        "name": "Test",
        "lastname": "Student",
        "student_code": "A1",
        "email": "short@student.edu.pl",
        "field_of_study_id": 1,
        "ects_points": 45,
    }

    response = client.post(f"{BASE_URL}/students", json=payload)

    assert response.status_code == 422
    body = response.json()
    assert body["detail"] == "Numer albumu studenta musi mieć długość od 5 do 10 znaków."


def test_post_students_rejects_ects_out_of_range_for_field(client, unique_student_code):
    payload = build_student_payload(unique_student_code)
    payload["field_of_study_id"] = 1
    payload["ects_points"] = 61

    response = client.post(f"{BASE_URL}/students", json=payload)

    assert response.status_code == 422
    body = response.json()
    assert body["detail"] == "Punkty ECTS wykraczają poza zakres dopuszczalny dla kierunku."


def test_delete_students_returns_204_and_student_is_no_longer_available(client, unique_student_code):
    create_payload = build_student_payload(unique_student_code)
    create_response = client.post(f"{BASE_URL}/students", json=create_payload)
    assert create_response.status_code == 201

    student_id = create_response.json()["id"]

    delete_response = client.delete(f"{BASE_URL}/students/{student_id}")
    assert delete_response.status_code == 204
    assert delete_response.text == ""

    get_response = client.get(f"{BASE_URL}/students/{student_id}")
    assert get_response.status_code == 404
    assert get_response.json()["detail"] == "Student not found"