import pytest

def test_student_cannot_post_official_notice(client, auth_headers):
    response = client.post(
        "/api/square/notices",
        json={
            "title": "Semester Exams",
            "body": "Exams start next week. Be prepared.",
            "category": "NOTICE"
        },
        headers=auth_headers
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

def test_student_can_post_peer_categories(client, auth_headers):
    response = client.post(
        "/api/square/notices",
        json={
            "title": "Looking for Roommate",
            "body": "Need a roommate for next semester.",
            "category": "ROOMMATE"
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["category"] == "ROOMMATE"
    assert data["author"]["role"] == "STUDENT"

def test_get_notices_and_filtering(client, auth_headers, auth_headers_staff):
    client.post(
        "/api/square/notices",
        json={"title": "Tech Fest", "body": "Annual Tech Fest is here!", "category": "EVENT"},
        headers=auth_headers_staff
    )
    client.post(
        "/api/square/notices",
        json={"title": "Lost Wallet", "body": "Lost a black wallet near the library.", "category": "LOST_FOUND"},
        headers=auth_headers
    )

    response_all = client.get("/api/square/notices", headers=auth_headers)
    assert response_all.status_code == 200
    assert len(response_all.json()) >= 2

    response_event = client.get("/api/square/notices?category=EVENT", headers=auth_headers)
    assert response_event.status_code == 200
    assert len(response_event.json()) == 1
    assert response_event.json()[0]["category"] == "EVENT"

def test_delete_own_notice(client, auth_headers):
    create_resp = client.post(
        "/api/square/notices",
        json={"title": "Found Keys", "body": "Found keys in cafeteria.", "category": "LOST_FOUND"},
        headers=auth_headers
    )
    notice_id = create_resp.json()["id"]

    del_resp = client.delete(f"/api/square/notices/{notice_id}", headers=auth_headers)
    assert del_resp.status_code == 200

def test_student_cannot_delete_others_notice(client, auth_headers, auth_headers_other_user):
    create_resp = client.post(
        "/api/square/notices",
        json={"title": "Ride to Airport", "body": "Leaving Friday at 5PM.", "category": "RIDE_POOL"},
        headers=auth_headers
    )
    notice_id = create_resp.json()["id"]

    del_resp = client.delete(f"/api/square/notices/{notice_id}", headers=auth_headers_other_user)
    assert del_resp.status_code == 403

def test_staff_can_delete_any_notice(client, auth_headers, auth_headers_staff):
    create_resp = client.post(
        "/api/square/notices",
        json={"title": "Ride to Airport", "body": "Leaving Friday at 5PM.", "category": "RIDE_POOL"},
        headers=auth_headers
    )
    notice_id = create_resp.json()["id"]

    del_resp = client.delete(f"/api/square/notices/{notice_id}", headers=auth_headers_staff)
    assert del_resp.status_code == 200

def test_add_and_delete_comment(client, auth_headers, auth_headers_other_user, auth_headers_staff):
    notice_resp = client.post(
        "/api/square/notices",
        json={"title": "Hackathon", "body": "Join the weekend hackathon.", "category": "EVENT"},
        headers=auth_headers_staff
    )
    notice_id = notice_resp.json()["id"]

    comment_resp = client.post(
        f"/api/square/notices/{notice_id}/comments",
        json={"text": "I'm excited for this!"},
        headers=auth_headers
    )
    assert comment_resp.status_code == 201
    comment_id = comment_resp.json()["id"]

    del_fail = client.delete(f"/api/square/comments/{comment_id}", headers=auth_headers_other_user)
    assert del_fail.status_code == 403

    del_success = client.delete(f"/api/square/comments/{comment_id}", headers=auth_headers_staff)
    assert del_success.status_code == 200