import pytest

def test_student_cannot_access_community_members(client, auth_headers):
    response = client.get("/api/community/members", headers=auth_headers)
    assert response.status_code == 403
    assert "Not authorized" in response.json()["detail"]

def test_head_can_access_community_members(client, auth_headers_staff, test_verified_user):
    response = client.get("/api/community/members", headers=auth_headers_staff)
    assert response.status_code == 200
    members = response.json()
    assert len(members) >= 1
    assert any(m["email"] == test_verified_user.email for m in members)

def test_head_can_update_member_role(client, auth_headers_staff, test_verified_user):
    user_id = test_verified_user.id
    response = client.patch(
        f"/api/community/members/{user_id}/role",
        json={"role": "CAPTAIN"},
        headers=auth_headers_staff
    )
    assert response.status_code == 200
    assert response.json()["role"] == "CAPTAIN"

def test_head_can_block_member(client, auth_headers_staff, test_other_user):
    user_id = test_other_user.id
    response = client.patch(
        f"/api/community/members/{user_id}/block",
        json={"is_blocked": True},
        headers=auth_headers_staff
    )
    assert response.status_code == 200
    assert response.json()["is_blocked"] is True

def test_head_can_update_roll_number(client, auth_headers_staff, test_verified_user):
    user_id = test_verified_user.id
    response = client.patch(
        f"/api/community/members/{user_id}/roll-number",
        json={"roll_number": "19CS3001"},
        headers=auth_headers_staff
    )
    assert response.status_code == 200
    assert response.json()["roll_number"] == "19CS3001"

def test_head_can_update_storage_limit(client, auth_headers_staff, test_verified_user):
    user_id = test_verified_user.id
    response = client.patch(
        f"/api/community/members/{user_id}/storage-limit",
        json={"storage_limit_mb": 100},
        headers=auth_headers_staff
    )
    assert response.status_code == 200
    assert response.json()["storage_limit"] == 100 * 1024 * 1024

def test_trigger_auto_roll_numbers(client, auth_headers_staff):
    response = client.post(
        "/api/community/settings/auto-roll-numbers",
        json={"extract_roll_from_email": True},
        headers=auth_headers_staff
    )
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["extract_roll_from_email"] is True