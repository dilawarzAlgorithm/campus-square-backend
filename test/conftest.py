import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta, timezone

from app.main import app
from app.core.config.config import settings
from app.core.database.database import get_db, Base
from app.models import models

SQLALCHEMY_DATABASE_URL = f"postgresql+psycopg://{settings.database_username}:{settings.database_password}@{settings.database_hostname}:{settings.database_port}/{settings.database_name}_test"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            db.close() 
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)



@pytest.fixture()
def test_institution(db):
    inst = models.Institution(
        id="test-institution-id-999",
        name="College Of Mine",
        short_name="COM",
        domain="college.com"
    )
    db.add(inst)
    db.commit()
    db.refresh(inst)
    return inst

@pytest.fixture()
def test_unverified_user(db, test_institution):
    from app.core.features.utils import hash
    
    unverified_user = models.User(
        id="test-unverified-user-id-001",
        email="unverified@college.com",
        password_hash=hash("password123"),
        first_name="Unverified",
        last_name="Student",
        institution_id=test_institution.id,
        is_verified=False,
        verification_otp="123456",
        otp_expires_at=datetime.now(timezone.utc) + timedelta(minutes=15)
    )
    db.add(unverified_user)
    db.flush()

    profile = models.Profile(
        id="test-unverified-profile-id-001",
        user_id=unverified_user.id
    )
    db.add(profile)
    db.commit()
    db.refresh(unverified_user)
    return unverified_user

@pytest.fixture(scope="function")
def test_verified_user(db, test_institution):
    from app.core.features.utils import hash

    verified_user = models.User(
        id="test-verified-user-id-002",
        email="student1@college.com",
        password_hash=hash("password123"),
        first_name="Student",
        last_name="One",
        institution_id=test_institution.id,
        is_verified=True,
        verification_otp=None,
        otp_expires_at=None
    )
    db.add(verified_user)
    db.flush()

    profile = models.Profile(
        id="test-verified-profile-id-002",
        user_id=verified_user.id
    )
    db.add(profile)
    db.commit()
    db.refresh(verified_user)
    return verified_user