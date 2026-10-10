import pytest

def test_create_alert_success(client, auth_headers):
    response = client.post(
        "/api/alerts",
        json={"message": "This is an important anonymous alert!"},
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["message"] == "This is an important anonymous alert!"
    assert "sender_id" not in data

def test_create_alert_validation_fail(client, auth_headers):
    response = client.post(
        "/api/alerts",
        json={"message": "Hi"},
        headers=auth_headers
    )
    assert response.status_code == 422
    assert "String should have at least 5 characters" in response.json()["detail"][0]["msg"]

def test_get_alerts(client, auth_headers):
    client.post(
        "/api/alerts",
        json={"message": "Alert for GET test"},
        headers=auth_headers
    )
    
    response = client.get("/api/alerts", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) >= 1
    assert "message" in data[0]
    assert "sender_id" not in data[0]

def test_student_cannot_block_sender(client, auth_headers, auth_headers_other_user):
    create_resp = client.post(
        "/api/alerts",
        json={"message": "Student block test alert"},
        headers=auth_headers
    )
    alert_id = create_resp.json()["id"]

    block_resp = client.post(
        f"/api/alerts/{alert_id}/block-sender",
        headers=auth_headers_other_user
    )
    assert block_resp.status_code == 403
    assert "Only administration can block" in block_resp.json()["detail"]

def test_staff_can_block_sender_and_prevent_future_alerts(client, auth_headers, auth_headers_staff):
    create_resp = client.post(
        "/api/alerts",
        json={"message": "Staff block test alert"},
        headers=auth_headers
    )
    alert_id = create_resp.json()["id"]

    block_resp = client.post(
        f"/api/alerts/{alert_id}/block-sender",
        headers=auth_headers_staff
    )
    assert block_resp.status_code == 200
    assert block_resp.json()["success"] is True

    second_alert_resp = client.post(
        "/api/alerts",
        json={"message": "Trying to send again after being blocked"},
        headers=auth_headers
    )
    assert second_alert_resp.status_code == 403
    assert "suspended" in second_alert_resp.json()["detail"].lower()