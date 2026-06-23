from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, ForeignKey, Enum as SQLEnum, TIMESTAMP, text
from sqlalchemy.orm import relationship

from app.core.database.database import Base
from app.enum.enum import ResourceType, VoteType

class Department(Base):
    __tablename__ = "departments"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    code = Column(String, nullable=False)
    
    institution_id = Column(String, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False)
    institution = relationship("Institution", back_populates="departments")

    resources = relationship("AcademicResource", back_populates="department", cascade="all, delete-orphan")


class AcademicResource(Base):
    __tablename__ = "academic_resources"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    file_url = Column(String, nullable=False)
    resource_type = Column(SQLEnum(ResourceType), default=ResourceType.NOTE, nullable=False)
    semester = Column(Integer, nullable=False)

    upvote_count = Column(Integer, default=0, nullable=False)
    downvote_count = Column(Integer, default=0, nullable=False)

    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    department_id = Column(String, ForeignKey("departments.id", ondelete="CASCADE"), nullable=False)
    department = relationship("Department", back_populates="resources")

    uploader_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    uploader = relationship("User", back_populates="uploaded_resources")

    votes = relationship("ResourceVote", back_populates="resource", cascade="all, delete-orphan")


class ResourceVote(Base):
    __tablename__ = "resource_votes"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    resource_id = Column(String, ForeignKey("academic_resources.id", ondelete="CASCADE"), nullable=False)
    vote_type = Column(SQLEnum(VoteType), nullable=False)

    user = relationship("User", back_populates="resource_votes")
    resource = relationship("AcademicResource", back_populates="votes")