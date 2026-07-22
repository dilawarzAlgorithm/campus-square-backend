import pytest
from app.models import models

@pytest.mark.parametrize(
    "registration_data, expected_status, detail_snippet",
    [
        ({
            "email": "student1@college.com",
            "password": "short",
            "first_name": "Test",
            "last_name": "User",
            "department_id": "some-id"
        }, 422, "at least 8 characters"),
        ({
            "email": "not-an-email-format",
            "password": "password123",
            "first_name": "Test",
            "last_name": "User",
            "department_id": "some-id"
        }, 422, "value is not a valid email address"),
        ({
            "email": "student1@college.com",
            "password": "password123",
            "first_name": "Test",
            "department_id": "some-id"
            # missing last_name
        }, 422, "Field required")
    ]
)
def test_registration_validation_failures(client, registration_data, expected_status, detail_snippet):
    response = client.post("/api/auth/register", json=registration_data)
    assert response.status_code == expected_status
    error_msg = str(response.json()["detail"])
    assert detail_snippet.lower() in error_msg.lower()

def test_registration_fails_without_department(client, test_institution):
    """Students MUST provide a department ID to register."""
    response = client.post(
        "/api/auth/register",
        json={
            "email": "nodepartment@college.com",
            "password": "password123",
            "first_name": "No",
            "last_name": "Department"
        }
    )
    assert response.status_code == 400
    assert "department selection is required" in response.json()["detail"].lower()

def test_registration_fails_unrecognized_domain(client):
    """Since the top-down model is implemented, unregistered domains trigger a 400."""
    response = client.post(
        "/api/auth/register",
        json={
            "email": "student1@unregistered.edu",
            "password": "password123",
            "first_name": "New",
            "last_name": "Student",
            "department_id": "fake-id"
        }
    )
    assert response.status_code == 400
    assert "not yet registered" in response.json()["detail"].lower()

def test_successful_student_registration(client, db, test_institution, test_department):
    response = client.post(
        "/api/auth/register",
        json={
            "email": "student99@college.com",
            "password": "password123",
            "first_name": "Student",
            "last_name": "NinetyNine",
            "department_id": test_department.id
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert "user_id" in data

    user = db.query(models.User).filter(models.User.email == "student99@college.com").first()
    assert user is not None
    assert user.is_verified is False
    assert user.department_id == test_department.id

@pytest.mark.parametrize(
    "email, otp, expected_status, expected_detail",
    [
        ("unverified@college.com", "999999", 400, "Invalid OTP code."),
        ("unregistered@college.com", "123456", 404, "User not found."),
        ("invalid-email-string", "123456", 422, "value is not a valid email address")
    ]
)
def test_otp_verification_failures(client, test_unverified_user, email, otp, expected_status, expected_detail):
    response = client.post("/api/auth/verify-otp", json={"email": email, "otp": otp})
    assert response.status_code == expected_status
    if expected_status != 422:
        assert response.json()["detail"] == expected_detail

def test_successful_otp_verification_and_login_pipeline(client, test_unverified_user):
    email = test_unverified_user.email
    otp_code = test_unverified_user.verification_otp

    verify_response = client.post("/api/auth/verify-otp", json={"email": email, "otp": otp_code})
    assert verify_response.status_code == 200
    assert verify_response.json()["success"] is True

    login_response = client.post("/api/auth/login", json={"email": email, "password": "password123"})
    assert login_response.status_code == 200
    tokens = login_response.json()
    assert "access_token" in tokens

@pytest.mark.parametrize(
    "email, password, expected_status, expected_detail",
    [
        ("student1@college.com", "incorrect_password", 401, "Incorrect email or password."),
        ("unregistered@college.com", "password123", 401, "Incorrect email or password."),
        ("unverified@college.com", "password123", 403, "not verified")
    ]
)
def test_login_validation_failures(client, test_verified_user, test_unverified_user, email, password, expected_status, expected_detail):
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == expected_status
    assert expected_detail.lower() in response.json()["detail"].lower()

def test_refresh_token_rotation(client, test_verified_user, db):
    login_response = client.post("/api/auth/login", json={"email": test_verified_user.email, "password": "password123"})
    assert login_response.status_code == 200
    first_refresh_token = login_response.json()["refresh_token"]

    refresh_response = client.post("/api/auth/refresh", json={"refresh_token": first_refresh_token})
    assert refresh_response.status_code == 200
    assert refresh_response.json()["refresh_token"] != first_refresh_token

    reuse_response = client.post("/api/auth/refresh", json={"refresh_token": first_refresh_token})
    assert reuse_response.status_code == 401