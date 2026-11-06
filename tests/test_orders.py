"""Tests for the orders endpoints (create, read, list)."""




def test_create_order_returns_generated_id_and_timestamp(client):
    response = client.post(
        "/orders",
        json={"item_name": "Widget", "quantity": 3},
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert "id" in data and data["id"]
    assert data["item_name"] == "Widget"
    assert data["quantity"] == 3
    assert "created_at" in data
    # Round-trip the ID through GET.
    get_response = client.get(f"/orders/{data['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == data["id"]


def test_create_order_rejects_empty_item_name(client):
    response = client.post("/orders", json={"item_name": "", "quantity": 1})
    assert response.status_code == 422, response.text


def test_create_order_rejects_missing_item_name(client):
    response = client.post("/orders", json={"quantity": 1})
    assert response.status_code == 422, response.text


def test_create_order_rejects_zero_quantity(client):
    response = client.post("/orders", json={"item_name": "Widget", "quantity": 0})
    assert response.status_code == 422, response.text


def test_create_order_rejects_negative_quantity(client):
    response = client.post("/orders", json={"item_name": "Widget", "quantity": -5})
    assert response.status_code == 422, response.text


def test_create_order_rejects_quantity_above_cap(client):
    response = client.post("/orders", json={"item_name": "Widget", "quantity": 10_001})
    assert response.status_code == 422, response.text


def test_get_order_returns_404_for_absent_id(client):
    response = client.get("/orders/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404, response.text
    assert "detail" in response.json()


def test_list_orders_default_page(client):
    client.post("/orders", json={"item_name": "A", "quantity": 1})
    client.post("/orders", json={"item_name": "B", "quantity": 2})
    response = client.get("/orders")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert data["page"] == 1
    assert data["page_size"] == 50
    assert len(data["orders"]) == 2


def test_list_orders_pagination(client):
    for i in range(5):
        client.post("/orders", json={"item_name": f"Item {i}", "quantity": i + 1})
    response = client.get("/orders", params={"page": 1, "page_size": 2})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert len(data["orders"]) == 2


def test_list_orders_page_size_capped(client):
    response = client.get("/orders", params={"page_size": 999})
    assert response.status_code == 422, response.text


def test_list_orders_empty(client):
    response = client.get("/orders")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["orders"] == []
