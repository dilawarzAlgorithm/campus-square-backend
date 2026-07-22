import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta, timezone

from app.main import app
from app.core.config.config import settings
from app.core.database.database import get_db, Base
from app.models import models
from app.core.features.utils import hash
from app.enum.enum import UserRole

SQLALCHEMY_DATABASE_URL = f"postgresql+psycopg://{settings.database_username}:{settings.database_password}@{settings.database_hostname}:{settings.database_port}/{settings.database_name}_test"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def db_engine():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()

@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass 
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def test_institution(db):
    inst = models.Institution(
        id=str(uuid.uuid4()),
        name="College Of Mine",
        short_name="COM",
        domain="college.com"
    )
    db.add(inst)
    db.commit()
    db.refresh(inst)
    return inst

@pytest.fixture(scope="function")
def test_department(db, test_institution):
    dept = models.Department(
        id=str(uuid.uuid4()),
        name="Computer Science",
        code="CSE",
        institution_id=test_institution.id
    )
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return dept

@pytest.fixture(scope="function")
def test_unverified_user(db, test_institution, test_department):
    unverified_user = models.User(
        id=str(uuid.uuid4()),
        email="unverified@college.com",
        password_hash=hash("password123"),
        first_name="Unverified",
        last_name="Student",
        institution_id=test_institution.id,
        department_id=test_department.id,
        is_verified=False,
        verification_otp="123456",
        otp_expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
        role=UserRole.STUDENT
    )
    db.add(unverified_user)
    db.flush()

    profile = models.Profile(id=str(uuid.uuid4()), user_id=unverified_user.id)
    db.add(profile)
    db.commit()
    db.refresh(unverified_user)
    return unverified_user

@pytest.fixture(scope="function")
def test_verified_user(db, test_institution, test_department):
    verified_user = models.User(
        id=str(uuid.uuid4()),
        email="student1@college.com",
        password_hash=hash("password123"),
        first_name="Student",
        last_name="One",
        institution_id=test_institution.id,
        department_id=test_department.id,
        is_verified=True,
        role=UserRole.STUDENT
    )
    db.add(verified_user)
    db.flush()

    profile = models.Profile(id=str(uuid.uuid4()), user_id=verified_user.id)
    db.add(profile)
    db.commit()
    db.refresh(verified_user)
    return verified_user

@pytest.fixture(scope="function")
def test_staff_user(db, test_institution):
    staff = models.User(
        id=str(uuid.uuid4()),
        email="staff@college.com",
        password_hash=hash("password123"),
        first_name="Community",
        last_name="Head",
        institution_id=test_institution.id,
        is_verified=True,
        role=UserRole.COMMUNITY_HEAD
    )
    db.add(staff)
    db.flush()

    profile = models.Profile(id=str(uuid.uuid4()), user_id=staff.id)
    db.add(profile)
    db.commit()
    db.refresh(staff)
    return staff

@pytest.fixture(scope="function")
def auth_headers(client, test_verified_user):
    response = client.post(
        "/api/auth/login",
        json={"email": test_verified_user.email, "password": "password123"}
    )
    return {"Authorization": f"Bearer {response.json()['access_token']}"}

@pytest.fixture(scope="function")
def auth_headers_staff(client, test_staff_user):
    response = client.post(
        "/api/auth/login-staff", 
        json={"email": test_staff_user.email, "password": "password123"}
    )
    return {"Authorization": f"Bearer {response.json()['access_token']}"}

@pytest.fixture(scope="function")
def auth_headers_other_user(client, db, test_institution, test_department):
    other_user = models.User(
        id=str(uuid.uuid4()),
        email="student2@college.com",
        password_hash=hash("password123"),
        first_name="Second",
        last_name="Student",
        institution_id=test_institution.id,
        department_id=test_department.id,
        is_verified=True,
        role=UserRole.STUDENT
    )
    db.add(other_user)
    db.commit()
    
    response = client.post(
        "/api/auth/login", 
        json={"email": "student2@college.com", "password": "password123"}
    )
    return {"Authorization": f"Bearer {response.json()['access_token']}"}