from typing import Optional, List
from pydantic import BaseModel
from datetime import date, time
from app.enum.enum import AttendanceStatus

class SubjectCreate(BaseModel):
    name: str
    code: Optional[str] = None
    attendance_policy: float = 75.0
    start_date: date
    end_date: date

class SubjectUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    attendance_policy: Optional[float] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None

class SubjectDashboardResponse(BaseModel):
    id: str
    name: str
    code: Optional[str]
    attendance_policy: float
    start_date: date
    end_date: date
    attended: int
    missed: int
    cancelled: int
    total_expected: int
    can_miss: int
    
    class Config:
        from_attributes = True

class TimetableEventCreate(BaseModel):
    subject_id: str
    title: str
    location: Optional[str] = None
    type: str
    day_of_week: int
    start_time: time
    end_time: time

class TimetableEventResponse(BaseModel):
    id: str
    subject_id: str
    title: str
    location: Optional[str] = None
    type: str
    day_of_week: int
    start_time: time
    end_time: time
    
    class Config:
        from_attributes = True

class AttendanceMark(BaseModel):
    event_id: str
    date: date
    status: AttendanceStatus

class AttendanceRecordResponse(BaseModel):
    id: str
    event_id: str
    date: date
    status: AttendanceStatus
    event_title: str
    event_type: str
    subject_name: str
    
    class Config:
        from_attributes = True