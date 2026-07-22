import pytest
import uuid

@pytest.fixture
def test_resources(client, auth_headers, test_department):
    r1 = client.post(
        "/api/vault/resources", 
        json={
            "title": "Semester 1 Notes", 
            "description": "Basic math",
            "file_url": "https://example.com/math.pdf", 
            "resource_type": "NOTE", 
            "semester": 1, 
            "department_id": test_department.id
        }, 
        headers=auth_headers
    ).json()
    
    r2 = client.post(
        "/api/vault/resources", 
        json={
            "title": "Semester 3 PYQs", 
            "file_url": "https://example.com/pyq.pdf", 
            "resource_type": "PYQ", 
            "semester": 3, 
            "department_id": test_department.id
        }, 
        headers=auth_headers
    ).json()
    return [r1, r2]

def test_student_cannot_create_department(client, auth_headers):
    """Ensure standard students cannot create new departments."""
    response = client.post(
        "/api/vault/departments",
        json={"name": "Hacking", "code": "HCK"},
        headers=auth_headers
    )
    assert response.status_code == 403
    assert "Only Community Heads" in response.json()["detail"]

def test_staff_can_create_department(client, auth_headers_staff):
    response = client.post(
        "/api/vault/departments",
        json={"name": "Electrical Engineering", "code": "EE"},
        headers=auth_headers_staff
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Electrical Engineering"
    assert data["code"] == "EE"

def test_create_duplicate_department(client, auth_headers_staff, test_department):
    response = client.post(
        "/api/vault/departments",
        json={"name": "Another CS", "code": test_department.code},
        headers=auth_headers_staff
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]

def test_get_departments(client, auth_headers, test_department):
    response = client.get("/api/vault/departments", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(d["code"] == test_department.code for d in data)

def test_create_resource(client, auth_headers, test_department):
    response = client.post(
        "/api/vault/resources",
        json={
            "title": "Data Structures Book",
            "description": "Official textbook",
            "file_url": "https://example.com/dsa.pdf",
            "resource_type": "OTHER",
            "semester": 4,
            "department_id": test_department.id
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Data Structures Book"
    assert data["upvote_count"] == 0

def test_create_resource_invalid_department(client, auth_headers):
    response = client.post(
        "/api/vault/resources",
        json={
            "title": "Orphaned Notes",
            "file_url": "https://example.com/orphaned.pdf",
            "resource_type": "NOTE",
            "semester": 1,
            "department_id": str(uuid.uuid4())
        },
        headers=auth_headers
    )
    assert response.status_code == 404

def test_get_resources_with_filters(client, auth_headers, test_resources):
    response_sem = client.get(f"/api/vault/resources?semester=3", headers=auth_headers)
    assert response_sem.status_code == 200
    assert len(response_sem.json()) == 1
    assert response_sem.json()[0]["title"] == "Semester 3 PYQs"

    response_type = client.get(f"/api/vault/resources?resource_type=NOTE", headers=auth_headers)
    assert response_type.status_code == 200
    assert len(response_type.json()) == 1

def test_voting_mechanics(client, auth_headers, test_resources):
    res_id = test_resources[0]["id"]
    
    resp_up = client.post(f"/api/vault/resources/{res_id}/vote", json={"vote_type": "UPVOTE"}, headers=auth_headers)
    assert resp_up.status_code == 200
    assert resp_up.json()["upvote_count"] == 1
    
    resp_down = client.post(f"/api/vault/resources/{res_id}/vote", json={"vote_type": "DOWNVOTE"}, headers=auth_headers)
    assert resp_down.status_code == 200
    assert resp_down.json()["upvote_count"] == 0
    assert resp_down.json()["downvote_count"] == 1

def test_delete_own_resource(client, auth_headers, test_resources):
    res_id = test_resources[0]["id"]
    response = client.delete(f"/api/vault/resources/{res_id}", headers=auth_headers)
    assert response.status_code == 200
    
    get_resp = client.get("/api/vault/resources", headers=auth_headers)
    assert len(get_resp.json()) == len(test_resources) - 1

def test_prevent_deleting_others_resource(client, auth_headers_other_user, test_resources):
    res_id = test_resources[0]["id"]
    response = client.delete(f"/api/vault/resources/{res_id}", headers=auth_headers_other_user)
    assert response.status_code == 403