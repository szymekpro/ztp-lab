BASE_URL = "api/v1/product"


def build_product_payload(product_name: str) -> dict:
    return {
        "name": product_name,
        "category_id": 1,
        "price": 299.99,
        "quantity": 10,
    }


def test_post_products_creates_product_and_history_entry(client, unique_product_name):
    payload = build_product_payload(unique_product_name)

    create_response = client.post(f"{BASE_URL}/products", json=payload)

    assert create_response.status_code == 201
    created = create_response.json()

    assert created["name"] == payload["name"]
    assert created["category"]["id"] == payload["category_id"]
    assert created["price"] == payload["price"]
    assert created["quantity"] == payload["quantity"]

    product_id = created["id"]

    history_response = client.get(f"{BASE_URL}/products/{product_id}/history")
    assert history_response.status_code == 200

    history = history_response.json()
    assert isinstance(history, list)
    assert len(history) >= 1

    latest_entry = history[0]
    assert latest_entry["product_id"] == product_id
    assert latest_entry["action"] == "CREATE"
    assert latest_entry["previous_state"] == {}
    assert latest_entry["current_state"]["name"] == payload["name"]


def test_post_products_rejects_forbidden_product_name(client, unique_product_name):
    payload = build_product_payload(unique_product_name)
    payload["name"] = f"test{unique_product_name}"

    response = client.post(f"{BASE_URL}/products", json=payload)

    assert response.status_code == 422
    body = response.json()
    assert body["detail"] == "Nazwa produktu zawiera zakazaną frazę."


def test_put_products_replaces_product_and_saves_history(client, unique_product_name):
    create_payload = build_product_payload(unique_product_name)
    create_response = client.post(f"{BASE_URL}/products", json=create_payload)
    assert create_response.status_code == 201

    product_id = create_response.json()["id"]

    replace_payload = {
        "name": f"{unique_product_name}X",
        "category_id": 2,
        "price": 199.99,
        "quantity": 5,
    }

    put_response = client.put(f"{BASE_URL}/products/{product_id}", json=replace_payload)

    assert put_response.status_code == 200
    replaced = put_response.json()

    assert replaced["id"] == product_id
    assert replaced["name"] == replace_payload["name"]
    assert replaced["category"]["id"] == replace_payload["category_id"]
    assert replaced["price"] == replace_payload["price"]
    assert replaced["quantity"] == replace_payload["quantity"]

    history_response = client.get(f"{BASE_URL}/products/{product_id}/history")
    assert history_response.status_code == 200

    history = history_response.json()
    assert len(history) >= 2

    latest_entry = history[0]
    create_entry = history[1]

    assert latest_entry["action"] == "REPLACE"
    assert latest_entry["previous_state"]["name"] == create_payload["name"]
    assert latest_entry["current_state"]["name"] == replace_payload["name"]

    assert create_entry["action"] == "CREATE"


def test_get_product_history_registers_patch_update(client, unique_product_name):
    create_payload = build_product_payload(unique_product_name)
    create_response = client.post(f"{BASE_URL}/products", json=create_payload)
    assert create_response.status_code == 201

    product_id = create_response.json()["id"]

    patch_payload = {
        "price": 499.99,
        "quantity": 20,
    }

    patch_response = client.patch(f"{BASE_URL}/products/{product_id}", json=patch_payload)

    assert patch_response.status_code == 200
    updated = patch_response.json()

    assert updated["id"] == product_id
    assert updated["price"] == patch_payload["price"]
    assert updated["quantity"] == patch_payload["quantity"]

    history_response = client.get(f"{BASE_URL}/products/{product_id}/history")
    assert history_response.status_code == 200

    history = history_response.json()
    assert len(history) >= 2

    latest_entry = history[0]
    assert latest_entry["action"] == "UPDATE"
    assert latest_entry["previous_state"]["price"] == create_payload["price"]
    assert latest_entry["current_state"]["price"] == patch_payload["price"]


def test_delete_products_saves_history_entry(client, unique_product_name):
    create_payload = build_product_payload(unique_product_name)
    create_response = client.post(f"{BASE_URL}/products", json=create_payload)
    assert create_response.status_code == 201

    product_id = create_response.json()["id"]

    delete_response = client.delete(f"{BASE_URL}/products/{product_id}")
    assert delete_response.status_code == 204

    history_response = client.get(f"{BASE_URL}/products/{product_id}/history")
    assert history_response.status_code == 200

    history = history_response.json()
    assert len(history) >= 2

    latest_entry = history[0]
    assert latest_entry["action"] == "DELETE"
    assert latest_entry["previous_state"]["name"] == create_payload["name"]
    assert latest_entry["current_state"] == {}
