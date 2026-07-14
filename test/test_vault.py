import pytest
import uuid

@pytest.fixture
def auth_headers(client, db, test_verified_user):
    test_verified_user = db.merge(test_verified_user)
    response = client.post(
        "/api/auth/login",
        json={"email": test_verified_user.email, "password": "password123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def auth_headers_other_user(client, db, test_institution, test_verified_user):
    from app.core.features.utils import hash
    from app.models import models
    
    test_institution = db.merge(test_institution)
    
    other_user = models.User(
        id=str(uuid.uuid4()),
        email="student2@college.com",
        password_hash=hash("password123"),
        first_name="Second",
        last_name="Student",
        institution_id=test_institution.id,
        is_verified=True
    )
    db.add(other_user)
    db.commit()
    
    response = client.post(
        "/api/auth/login", 
        json={"email": "student2@college.com", "password": "password123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def test_department(client, auth_headers):
    response = client.post(
        "/api/vault/departments",
        json={"name": "Computer Science", "code": "CSE"},
        headers=auth_headers
    )
    return response.json()

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
            "department_id": test_department["id"]
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
            "department_id": test_department["id"]
        }, 
        headers=auth_headers
    ).json()
    return [r1, r2]


def test_create_department(client, auth_headers):
    response = client.post(
        "/api/vault/departments",
        json={"name": "Electrical Engineering", "code": "EE"},
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Electrical Engineering"
    assert data["code"] == "EE"

def test_create_duplicate_department(client, auth_headers, test_department):
    response = client.post(
        "/api/vault/departments",
        json={"name": "Another CS", "code": "CSE"},
        headers=auth_headers
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]

def test_get_departments(client, auth_headers, test_department):
    response = client.get("/api/vault/departments", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(d["code"] == "CSE" for d in data)

def test_create_resource(client, auth_headers, test_department):
    response = client.post(
        "/api/vault/resources",
        json={
            "title": "Data Structures Book",
            "description": "Official textbook",
            "file_url": "https://example.com/dsa.pdf",
            "resource_type": "OTHER",
            "semester": 4,
            "department_id": test_department["id"]
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Data Structures Book"
    assert data["upvote_count"] == 0
    assert data["downvote_count"] == 0

def test_create_resource_invalid_department(client, auth_headers):
    response = client.post(
        "/api/vault/resources",
        json={
            "title": "Orphaned Notes",
            "file_url": "https://example.com/orphaned.pdf",
            "resource_type": "NOTE",
            "semester": 1,
            "department_id": "non-existent-uuid"
        },
        headers=auth_headers
    )
    assert response.status_code == 404

def test_get_resources_with_filters(client, auth_headers, test_department, test_resources):
    response_sem = client.get(f"/api/vault/resources?semester=3", headers=auth_headers)
    assert response_sem.status_code == 200
    data_sem = response_sem.json()
    assert len(data_sem) == 1
    assert data_sem[0]["title"] == "Semester 3 PYQs"

    response_type = client.get(f"/api/vault/resources?resource_type=NOTE", headers=auth_headers)
    assert response_type.status_code == 200
    assert len(response_type.json()) == 1
    assert response_type.json()[0]["title"] == "Semester 1 Notes"

def test_voting_mechanics(client, auth_headers, test_resources):
    res_id = test_resources[0]["id"]
    
    resp_up = client.post(f"/api/vault/resources/{res_id}/vote", json={"vote_type": "UPVOTE"}, headers=auth_headers)
    assert resp_up.status_code == 200
    assert resp_up.json()["upvote_count"] == 1
    assert resp_up.json()["downvote_count"] == 0
    
    resp_down = client.post(f"/api/vault/resources/{res_id}/vote", json={"vote_type": "DOWNVOTE"}, headers=auth_headers)
    assert resp_down.status_code == 200
    assert resp_down.json()["upvote_count"] == 0
    assert resp_down.json()["downvote_count"] == 1
    
    resp_toggle = client.post(f"/api/vault/resources/{res_id}/vote", json={"vote_type": "DOWNVOTE"}, headers=auth_headers)
    assert resp_toggle.status_code == 200
    assert resp_toggle.json()["upvote_count"] == 0
    assert resp_toggle.json()["downvote_count"] == 0

def test_delete_own_resource(client, auth_headers, test_resources):
    res_id = test_resources[0]["id"]
    
    response = client.delete(f"/api/vault/resources/{res_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["success"] is True
    
    get_resp = client.get("/api/vault/resources", headers=auth_headers)
    assert len(get_resp.json()) == len(test_resources) - 1

def test_prevent_deleting_others_resource(client, auth_headers_other_user, test_resources):
    res_id = test_resources[0]["id"]
    
    response = client.delete(f"/api/vault/resources/{res_id}", headers=auth_headers_other_user)
    assert response.status_code == 403
    assert "permission to delete" in response.json()["detail"]

def test_multi_user_voting_scenario(client, db, auth_headers, auth_headers_other_user, test_institution, test_resources):
    res_id = test_resources[0]["id"]
    
    def get_new_user_headers(email):
        from app.core.features.utils import hash
        from app.models import models
        import uuid
        
        merged_inst = db.merge(test_institution)
        
        user = models.User(
            id=str(uuid.uuid4()),
            email=email,
            password_hash=hash("password123"),
            first_name="Test",
            last_name="User",
            institution_id=merged_inst.id,
            is_verified=True
        )
        db.add(user)
        db.commit()
        
        resp = client.post("/api/auth/login", json={"email": email, "password": "password123"})
        return {"Authorization": f"Bearer {resp.json()['access_token']}"}

    headers_user3 = get_new_user_headers("user3@college.com")
    headers_user4 = get_new_user_headers("user4@college.com")

    r1 = client.post(f"/api/vault/resources/{res_id}/vote", json={"vote_type": "UPVOTE"}, headers=auth_headers)
    assert r1.status_code == 200
    assert r1.json()["upvote_count"] == 1
    assert r1.json()["downvote_count"] == 0

    r2 = client.post(f"/api/vault/resources/{res_id}/vote", json={"vote_type": "UPVOTE"}, headers=auth_headers_other_user)
    assert r2.status_code == 200
    assert r2.json()["upvote_count"] == 2
    assert r2.json()["downvote_count"] == 0

    r3 = client.post(f"/api/vault/resources/{res_id}/vote", json={"vote_type": "UPVOTE"}, headers=headers_user3)
    assert r3.status_code == 200
    assert r3.json()["upvote_count"] == 3
    assert r3.json()["downvote_count"] == 0

    r4 = client.post(f"/api/vault/resources/{res_id}/vote", json={"vote_type": "DOWNVOTE"}, headers=headers_user4)
    assert r4.status_code == 200
    assert r4.json()["upvote_count"] == 3
    assert r4.json()["downvote_count"] == 1

    final_resp = client.get("/api/vault/resources", headers=auth_headers)
    assert final_resp.status_code == 200
    
    resource = next(r for r in final_resp.json() if r["id"] == res_id)
    assert resource["upvote_count"] == 3
    assert resource["downvote_count"] == 1