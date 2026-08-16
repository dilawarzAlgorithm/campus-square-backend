import pytest

def test_non_admin_cannot_access_metrics(client, auth_headers_staff):
    response = client.get("/api/admin/metrics", headers=auth_headers_staff)
    assert response.status_code == 403
    assert "Global admin privileges required" in response.json()["detail"]

def test_admin_metrics(client, auth_headers_admin):
    response = client.get("/api/admin/metrics", headers=auth_headers_admin)
    assert response.status_code == 200
    metrics = response.json()
    assert "total_institutions" in metrics
    assert "total_users" in metrics

def test_get_institutions(client, auth_headers_admin):
    response = client.get("/api/admin/institutions", headers=auth_headers_admin)
    assert response.status_code == 200
    assert len(response.json()) >= 1

def test_create_institution(client, auth_headers_admin):
    response = client.post(
        "/api/admin/institutions",
        json={
            "name": "New University",
            "short_name": "NU",
            "domain": "newuniv.edu",
            "head_email": "head@newuniv.edu",
            "head_first_name": "New",
            "head_last_name": "Head",
            "head_password": "password123",
            "default_storage_limit_mb": 200
        },
        headers=auth_headers_admin
    )
    assert response.status_code == 201
    assert response.json()["name"] == "New University"

def test_update_institution_storage_limit(client, auth_headers_admin, test_institution):
    inst_id = test_institution.id
    response = client.patch(
        f"/api/admin/institutions/{inst_id}/storage-limit",
        json={"default_storage_limit_mb": 500},
        headers=auth_headers_admin
    )
    assert response.status_code == 200
    assert response.json()["default_storage_limit"] == 500 * 1024 * 1024

def test_get_all_users(client, auth_headers_admin):
    response = client.get("/api/admin/users", headers=auth_headers_admin)
    assert response.status_code == 200
    assert len(response.json()) >= 1

def test_block_user_by_admin(client, auth_headers_admin, test_verified_user):
    user_id = test_verified_user.id
    response = client.patch(
        f"/api/admin/users/{user_id}/block",
        json={"is_blocked": True},
        headers=auth_headers_admin
    )
    assert response.status_code == 200
    assert response.json()["is_blocked"] is True

def test_toggle_institution_block(client, auth_headers_admin, test_institution):
    inst_id = test_institution.id
    response = client.patch(
        f"/api/admin/institutions/{inst_id}/block",
        json={"is_blocked": True},
        headers=auth_headers_admin
    )
    assert response.status_code == 200
    assert response.json()["is_blocked"] is True

def test_delete_institution(client, auth_headers_admin, test_institution):
    inst_id = test_institution.id
    response = client.delete(
        f"/api/admin/institutions/{inst_id}",
        headers=auth_headers_admin
    )
    assert response.status_code == 200
    assert response.json()["success"] is True