import pytest
import uuid

@pytest.fixture
def auth_headers_student(client, db, test_institution):
    from app.core.features.utils import hash
    from app.models import models
    from app.enum.enum import UserRole
    
    merged_inst = db.merge(test_institution)
    
    user = models.User(
        id=str(uuid.uuid4()),
        email="student_square@college.com",
        password_hash=hash("password123"),
        first_name="Square",
        last_name="Student",
        institution_id=merged_inst.id,
        is_verified=True,
        role=UserRole.STUDENT
    )
    db.add(user)
    db.commit()
    
    response = client.post(
        "/api/auth/login", 
        json={"email": "student_square@college.com", "password": "password123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def auth_headers_other_student(client, db, test_institution):
    from app.core.features.utils import hash
    from app.models import models
    from app.enum.enum import UserRole
    
    merged_inst = db.merge(test_institution)
    
    user = models.User(
        id=str(uuid.uuid4()),
        email="student2_square@college.com",
        password_hash=hash("password123"),
        first_name="Other",
        last_name="Student",
        institution_id=merged_inst.id,
        is_verified=True,
        role=UserRole.STUDENT
    )
    db.add(user)
    db.commit()
    
    response = client.post(
        "/api/auth/login", 
        json={"email": "student2_square@college.com", "password": "password123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def auth_headers_staff(client, db, test_institution):
    from app.core.features.utils import hash
    from app.models import models
    from app.enum.enum import UserRole
    
    merged_inst = db.merge(test_institution)
    
    user = models.User(
        id=str(uuid.uuid4()),
        email="staff_square@college.com",
        password_hash=hash("password123"),
        first_name="Community",
        last_name="Head",
        institution_id=merged_inst.id,
        is_verified=True,
        role=UserRole.COMMUNITY_HEAD
    )
    db.add(user)
    db.commit()
    
    response = client.post(
        "/api/auth/login-staff", 
        json={"email": "staff_square@college.com", "password": "password123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_student_cannot_post_official_notice(client, auth_headers_student):
    response = client.post(
        "/api/square/notices",
        json={
            "title": "Semester Exams",
            "body": "Exams start next week. Be prepared.",
            "category": "NOTICE"
        },
        headers=auth_headers_student
    )
    assert response.status_code == 403
    assert "Only administrators and community heads" in response.json()["detail"]


def test_staff_can_post_official_notice(client, auth_headers_staff):
    response = client.post(
        "/api/square/notices",
        json={
            "title": "Semester Exams",
            "body": "Exams start next week. Be prepared.",
            "category": "NOTICE"
        },
        headers=auth_headers_staff
    )
    assert response.status_code == 201
    assert response.json()["category"] == "NOTICE"


def test_student_can_post_peer_categories(client, auth_headers_student):
    response = client.post(
        "/api/square/notices",
        json={
            "title": "Looking for Roommate",
            "body": "Need a roommate for next semester.",
            "category": "ROOMMATE"
        },
        headers=auth_headers_student
    )
    assert response.status_code == 201
    data = response.json()
    assert data["category"] == "ROOMMATE"
    assert data["author"]["role"] == "STUDENT"

def test_get_notices_and_filtering(client, auth_headers_student, auth_headers_staff):
    client.post(
        "/api/square/notices",
        json={"title": "Tech Fest", "body": "Annual Tech Fest is here!", "category": "EVENT"},
        headers=auth_headers_staff
    )
    client.post(
        "/api/square/notices",
        json={"title": "Lost Wallet", "body": "Lost a black wallet near the library.", "category": "LOST_FOUND"},
        headers=auth_headers_student
    )

    response_all = client.get("/api/square/notices", headers=auth_headers_student)
    assert response_all.status_code == 200
    assert len(response_all.json()) >= 2

    response_event = client.get("/api/square/notices?category=EVENT", headers=auth_headers_student)
    assert response_event.status_code == 200
    assert len(response_event.json()) == 1
    assert response_event.json()[0]["category"] == "EVENT"

    response_lost = client.get("/api/square/notices?category=LOST_FOUND", headers=auth_headers_student)
    assert response_lost.status_code == 200
    assert len(response_lost.json()) == 1
    assert response_lost.json()[0]["category"] == "LOST_FOUND"


def test_delete_own_notice(client, auth_headers_student):
    create_resp = client.post(
        "/api/square/notices",
        json={"title": "Found Keys", "body": "Found keys in cafeteria.", "category": "LOST_FOUND"},
        headers=auth_headers_student
    )
    notice_id = create_resp.json()["id"]

    del_resp = client.delete(f"/api/square/notices/{notice_id}", headers=auth_headers_student)
    assert del_resp.status_code == 200
    assert del_resp.json()["success"] is True


def test_student_cannot_delete_others_notice(client, auth_headers_student, auth_headers_other_student):
    create_resp = client.post(
        "/api/square/notices",
        json={"title": "Ride to Airport", "body": "Leaving Friday at 5PM.", "category": "RIDE_POOL"},
        headers=auth_headers_student
    )
    notice_id = create_resp.json()["id"]

    del_resp = client.delete(f"/api/square/notices/{notice_id}", headers=auth_headers_other_student)
    assert del_resp.status_code == 403
    assert "Not authorized" in del_resp.json()["detail"]


def test_staff_can_delete_any_notice(client, auth_headers_student, auth_headers_staff):
    create_resp = client.post(
        "/api/square/notices",
        json={"title": "Ride to Airport", "body": "Leaving Friday at 5PM.", "category": "RIDE_POOL"},
        headers=auth_headers_student
    )
    notice_id = create_resp.json()["id"]

    del_resp = client.delete(f"/api/square/notices/{notice_id}", headers=auth_headers_staff)
    assert del_resp.status_code == 200


def test_add_and_delete_comment(client, auth_headers_student, auth_headers_other_student, auth_headers_staff):
    notice_resp = client.post(
        "/api/square/notices",
        json={"title": "Hackathon", "body": "Join the weekend hackathon.", "category": "EVENT"},
        headers=auth_headers_staff
    )
    notice_id = notice_resp.json()["id"]

    comment_resp = client.post(
        f"/api/square/notices/{notice_id}/comments",
        json={"text": "I'm excited for this!"},
        headers=auth_headers_student
    )
    assert comment_resp.status_code == 201
    comment_id = comment_resp.json()["id"]
    assert comment_resp.json()["text"] == "I'm excited for this!"

    del_fail = client.delete(f"/api/square/comments/{comment_id}", headers=auth_headers_other_student)
    assert del_fail.status_code == 403

    del_success = client.delete(f"/api/square/comments/{comment_id}", headers=auth_headers_staff)
    assert del_success.status_code == 200
    assert del_success.json()["success"] is True