from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Date, Time, ForeignKey, Enum as SQLEnum, TIMESTAMP, text
from sqlalchemy.orm import relationship
from app.core.database.database import Base
from app.enum.enum import AttendanceStatus

class Subject(Base):
    __tablename__ = "subjects"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    code = Column(String, nullable=True)
    attendance_policy = Column(Float, default=75.0)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), nullable=False)

    user = relationship("User")
    events = relationship("TimetableEvent", back_populates="subject", cascade="all, delete-orphan")


class TimetableEvent(Base):
    __tablename__ = "timetable_events"
    
    id = Column(String, primary_key=True, index=True)
    subject_id = Column(String, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    location = Column(String, nullable=True)
    type = Column(String, nullable=False) # e.g., Class, Lab, Exam
    day_of_week = Column(Integer, nullable=False) # 1 = Monday, 7 = Sunday
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)

    subject = relationship("Subject", back_populates="events")
    attendance_records = relationship("AttendanceRecord", back_populates="event", cascade="all, delete-orphan")


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"
    
    id = Column(String, primary_key=True, index=True)
    event_id = Column(String, ForeignKey("timetable_events.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    status = Column(SQLEnum(AttendanceStatus), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), nullable=False)

    event = relationship("TimetableEvent", back_populates="attendance_records")
