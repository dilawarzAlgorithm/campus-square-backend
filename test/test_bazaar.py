import pytest

def test_create_product(client, auth_headers):
    response = client.post(
        "/api/bazaar/products",
        json={
            "title": "Calculus Textbook",
            "description": "Like new, used for one semester.",
            "price": 45.0,
            "category": "TEXTBOOK",
            "condition": "LIKE_NEW"
        },
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Calculus Textbook"
    assert data["price"] == 45.0
    assert data["category"] == "TEXTBOOK"

def test_get_products(client, auth_headers):
    client.post(
        "/api/bazaar/products",
        json={
            "title": "Desk Lamp",
            "description": "Works perfectly.",
            "price": 10.0,
            "category": "FURNITURE",
            "condition": "GOOD"
        },
        headers=auth_headers
    )
    
    response = client.get("/api/bazaar/products", headers=auth_headers)
    
    assert response.status_code == 200
    assert len(response.json()) >= 1
    
    response_filtered = client.get("/api/bazaar/products?category=FURNITURE", headers=auth_headers)
    assert response_filtered.status_code == 200
    assert all(p["category"] == "FURNITURE" for p in response_filtered.json())

def test_update_product(client, auth_headers):
    create_resp = client.post(
        "/api/bazaar/products",
        json={
            "title": "Old Laptop",
            "description": "Still runs fine.",
            "price": 150.0,
            "category": "ELECTRONICS",
            "condition": "FAIR"
        },
        headers=auth_headers
    )
    product_id = create_resp.json()["id"]
    
    update_resp = client.patch(
        f"/api/bazaar/products/{product_id}",
        json={"is_sold": True},
        headers=auth_headers
    )
    
    assert update_resp.status_code == 200
    assert update_resp.json()["is_sold"] is True

def test_delete_product(client, auth_headers):
    create_resp = client.post(
        "/api/bazaar/products",
        json={
            "title": "To be deleted",
            "description": "Will delete this soon.",
            "price": 5.0,
            "category": "OTHER",
            "condition": "NEW"
        },
        headers=auth_headers
    )
    product_id = create_resp.json()["id"]
    
    del_resp = client.delete(f"/api/bazaar/products/{product_id}", headers=auth_headers)
    
    assert del_resp.status_code == 200
    assert del_resp.json()["success"] is True

def test_save_product(client, auth_headers):
    create_resp = client.post(
        "/api/bazaar/products",
        json={
            "title": "Save this",
            "description": "Item to save",
            "price": 20.0,
            "category": "STATIONERY",
            "condition": "NEW"
        },
        headers=auth_headers
    )
    product_id = create_resp.json()["id"]
    
    save_resp = client.post(f"/api/bazaar/products/{product_id}/save", headers=auth_headers)
    
    assert save_resp.status_code == 200
    assert save_resp.json()["is_saved"] is True
    
    unsave_resp = client.post(f"/api/bazaar/products/{product_id}/save", headers=auth_headers)
    assert unsave_resp.status_code == 200
    assert unsave_resp.json()["is_saved"] is False