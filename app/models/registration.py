from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Enum as SQLEnum, TIMESTAMP, text
from sqlalchemy.orm import relationship

from app.core.database.database import Base
from app.enum.enum import UserRole

class Institution(Base):
    __tablename__ = "institutions"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    short_name = Column(String, nullable=False)
    domain = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    users = relationship("User", back_populates="institution", cascade="all, delete-orphan")
    departments = relationship("Department", back_populates="institution", cascade="all, delete-orphan")

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.STUDENT, nullable=False)
    is_verified = Column(Boolean, default=False)
    
    is_blocked = Column(Boolean, default=False) 
    requires_password_change = Column(Boolean, default=False)
    
    verification_otp = Column(String, nullable=True)
    otp_expires_at = Column(TIMESTAMP(timezone=True), nullable=True)
    
    karma = Column(Integer, default=0)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    institution_id = Column(String, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False)
    institution = relationship("Institution", back_populates="users")

    profile = relationship("Profile", uselist=False, back_populates="user", cascade="all, delete-orphan")
    
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    uploaded_resources = relationship("AcademicResource", back_populates="uploader", cascade="all, delete-orphan")
    resource_votes = relationship("ResourceVote", back_populates="user", cascade="all, delete-orphan")

class Profile(Base):
    __tablename__ = "profiles"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    dietary_preference = Column(String, nullable=True)  # "Veg", "Non-Veg"
    sleep_schedule = Column(String, nullable=True)      # "Night Owl", "Early Bird"
    study_habits = Column(String, nullable=True)        # "Group Study", "Quiet Study"

    user = relationship("User", back_populates="profile")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(String, primary_key=True, index=True)
    token = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    expires_at = Column(TIMESTAMP(timezone=True), nullable=False)
    revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), nullable=False)

    user = relationship("User", back_populates="refresh_tokens")