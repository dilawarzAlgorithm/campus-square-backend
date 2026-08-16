import pytest

def test_create_subject(client, auth_headers):
    response = client.post(
        "/api/timetable/subjects",
        json={
            "name": "Mathematics",
            "code": "MATH101",
            "attendance_policy": 75.0,
            "start_date": "2024-01-01",
            "end_date": "2024-05-01"
        },
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Mathematics"
    assert data["code"] == "MATH101"
    assert data["attendance_policy"] == 75.0

def test_create_subject_invalid_dates(client, auth_headers):
    response = client.post(
        "/api/timetable/subjects",
        json={
            "name": "History",
            "start_date": "2024-05-01",
            "end_date": "2024-01-01"
        },
        headers=auth_headers
    )
    assert response.status_code == 400
    assert "after start date" in response.json()["detail"].lower()

def test_get_subjects(client, auth_headers):
    client.post(
        "/api/timetable/subjects",
        json={
            "name": "Physics",
            "start_date": "2024-01-01",
            "end_date": "2024-05-01"
        },
        headers=auth_headers
    )
    response = client.get("/api/timetable/subjects", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) >= 1
    assert "total_expected" in response.json()[0]
    assert "can_miss" in response.json()[0]

def test_update_subject(client, auth_headers):
    create_resp = client.post(
        "/api/timetable/subjects",
        json={
            "name": "Chemistry",
            "start_date": "2024-01-01",
            "end_date": "2024-05-01"
        },
        headers=auth_headers
    )
    sub_id = create_resp.json()["id"]

    update_resp = client.patch(
        f"/api/timetable/subjects/{sub_id}",
        json={"name": "Advanced Chemistry", "attendance_policy": 80.0},
        headers=auth_headers
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "Advanced Chemistry"
    assert update_resp.json()["attendance_policy"] == 80.0

def test_delete_subject(client, auth_headers):
    create_resp = client.post(
        "/api/timetable/subjects",
        json={
            "name": "Biology",
            "start_date": "2024-01-01",
            "end_date": "2024-05-01"
        },
        headers=auth_headers
    )
    sub_id = create_resp.json()["id"]

    del_resp = client.delete(f"/api/timetable/subjects/{sub_id}", headers=auth_headers)
    assert del_resp.status_code == 200
    assert del_resp.json()["success"] is True

    get_resp = client.get("/api/timetable/subjects", headers=auth_headers)
    assert not any(s["id"] == sub_id for s in get_resp.json())

def test_timetable_events_and_attendance_flow(client, auth_headers):
    
    sub_resp = client.post(
        "/api/timetable/subjects",
        json={
            "name": "Computer Science",
            "start_date": "2024-01-01",
            "end_date": "2024-05-01"
        },
        headers=auth_headers
    )
    sub_id = sub_resp.json()["id"]

    ev_resp = client.post(
        "/api/timetable/events",
        json={
            "subject_id": sub_id,
            "title": "CS Lecture",
            "location": "Room 101",
            "type": "Class",
            "day_of_week": 1,
            "start_time": "10:00:00",
            "end_time": "11:00:00"
        },
        headers=auth_headers
    )
    assert ev_resp.status_code == 200
    ev_id = ev_resp.json()["id"]

    get_ev = client.get("/api/timetable/events", headers=auth_headers)
    assert get_ev.status_code == 200
    assert any(e["id"] == ev_id for e in get_ev.json())

    att_resp = client.post(
        "/api/timetable/attendance",
        json={
            "event_id": ev_id,
            "date": "2024-01-01",
            "status": "ATTENDED"
        },
        headers=auth_headers
    )
    assert att_resp.status_code == 200

    att_resp_update = client.post(
        "/api/timetable/attendance",
        json={
            "event_id": ev_id,
            "date": "2024-01-01",
            "status": "MISSED"
        },
        headers=auth_headers
    )
    assert att_resp_update.status_code == 200

    hist_resp = client.get(f"/api/timetable/attendance/subject/{sub_id}", headers=auth_headers)
    assert hist_resp.status_code == 200
    records = hist_resp.json()
    assert len(records) == 1
    assert records[0]["status"] == "MISSED"
    assert records[0]["event_title"] == "CS Lecture"
    rec_id = records[0]["id"]

    del_att = client.delete(f"/api/timetable/attendance/{rec_id}", headers=auth_headers)
    assert del_att.status_code == 200

    del_ev = client.delete(f"/api/timetable/events/{ev_id}", headers=auth_headers)
    assert del_ev.status_code == 200