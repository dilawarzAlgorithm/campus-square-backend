import pytest

def test_student_cannot_create_club(client, auth_headers):
    response = client.post("/api/hubs", json={
        "name": "Student Hacker Club",
        "description": "Hackers only",
        "type": "CLUB",
        "privacy": "PUBLIC"
    }, headers=auth_headers)
    assert response.status_code == 403
    assert "Only staff can create official clubs" in response.json()["detail"]

def test_staff_can_create_club(client, auth_headers_staff):
    response = client.post("/api/hubs", json={
        "name": "Official Tech Club",
        "description": "Tech enthusiasts",
        "type": "CLUB",
        "privacy": "PUBLIC"
    }, headers=auth_headers_staff)
    assert response.status_code == 200
    assert response.json()["is_admin"] is True

def test_student_can_create_study_group(client, auth_headers):
    response = client.post("/api/hubs", json={
        "name": "Physics Study",
        "description": "Midterm prep",
        "type": "STUDY_GROUP",
        "privacy": "PUBLIC"
    }, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["type"] == "STUDY_GROUP"

def test_join_private_hub(client, auth_headers_staff, auth_headers):
    club = client.post("/api/hubs", json={
        "name": "Secret Club",
        "description": "Shh",
        "type": "CLUB",
        "privacy": "PRIVATE"
    }, headers=auth_headers_staff).json()

    join_response = client.post(f"/api/hubs/{club['id']}/join", headers=auth_headers)
    assert join_response.status_code == 200
    assert join_response.json()["is_pending"] is True

def test_create_team_and_assign_lead(client, auth_headers_staff, auth_headers, test_verified_user):
    club = client.post("/api/hubs", json={
        "name": "Robotics Club",
        "description": "Bots",
        "type": "CLUB",
        "privacy": "PUBLIC"
    }, headers=auth_headers_staff).json()

    team = client.post("/api/hubs", json={
        "name": "Software Team",
        "description": "Code",
        "type": "TEAM",
        "privacy": "PRIVATE",
        "parent_id": club["id"]
    }, headers=auth_headers_staff).json()
    assert team["parent_id"] == club["id"]

    # Deliberately NOT calling join here to test the auto-join logic in the make-lead endpoint
    lead_response = client.patch(
        f"/api/hubs/{team['id']}/members/{test_verified_user.id}/make-lead", 
        headers=auth_headers_staff
    )
    assert lead_response.status_code == 200
    assert lead_response.json()["success"] is True

    remove_response = client.patch(
        f"/api/hubs/{team['id']}/members/{test_verified_user.id}/remove-lead", 
        headers=auth_headers_staff
    )
    assert remove_response.status_code == 200
    assert remove_response.json()["success"] is True

def test_delete_hub_by_staff(client, auth_headers_staff):
    club = client.post("/api/hubs", json={
        "name": "To Be Deleted Club",
        "description": "Will delete this soon.",
        "type": "CLUB",
        "privacy": "PUBLIC"
    }, headers=auth_headers_staff).json()
    
    del_resp = client.delete(f"/api/hubs/{club['id']}", headers=auth_headers_staff)
    assert del_resp.status_code == 200
    assert del_resp.json()["success"] is True

def test_delete_hub_unauthorized(client, auth_headers_staff, auth_headers):
    club = client.post("/api/hubs", json={
        "name": "Staff Only Hub",
        "description": "Important stuff.",
        "type": "CLUB",
        "privacy": "PUBLIC"
    }, headers=auth_headers_staff).json()
    
    del_resp = client.delete(f"/api/hubs/{club['id']}", headers=auth_headers)
    assert del_resp.status_code == 403
    assert "Not authorized to delete this group" in del_resp.json()["detail"]

def test_get_hubs(client, auth_headers_staff):
    response = client.get("/api/hubs", headers=auth_headers_staff)
    assert response.status_code == 200
    assert isinstance(response.json(), list)