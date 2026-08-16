import uuid
import math
from datetime import date, timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database.database import get_db
from app.models import models
from app.schemas import timetable as schemas
from app.core.auth.oauth2 import get_current_user
from app.enum.enum import AttendanceStatus

router = APIRouter(prefix="/api/timetable", tags=["Timetable & Attendance"])

def count_weekdays(start_date: date, end_date: date, app_weekday: int) -> int:
    target_py_weekday = app_weekday - 1
    days_diff = (end_date - start_date).days
    if days_diff < 0: return 0
    count = days_diff // 7
    rem = days_diff % 7
    for i in range(rem + 1):
        if (start_date + timedelta(days=i)).weekday() == target_py_weekday:
            count += 1
    return count

def get_subject_dashboard_metrics(sub: models.Subject, current_user_id: str, db: Session) -> schemas.SubjectDashboardResponse:
    events = db.query(models.TimetableEvent).filter(models.TimetableEvent.subject_id == sub.id).all()
    total_expected = sum(count_weekdays(sub.start_date, sub.end_date, e.day_of_week) for e in events)
    
    records = db.query(models.AttendanceRecord).join(models.TimetableEvent).filter(
        models.TimetableEvent.subject_id == sub.id,
        models.AttendanceRecord.user_id == current_user_id
    ).all()
    
    attended = sum(1 for r in records if r.status == AttendanceStatus.ATTENDED)
    missed = sum(1 for r in records if r.status == AttendanceStatus.MISSED)
    cancelled = sum(1 for r in records if r.status == AttendanceStatus.CANCELLED)
    
    effective_total = max(0, total_expected - cancelled)
    required_classes = math.ceil(effective_total * (sub.attendance_policy / 100))
    can_miss = max(0, effective_total - required_classes - missed)
    
    return schemas.SubjectDashboardResponse(
        id=sub.id, name=sub.name, code=sub.code,
        attendance_policy=sub.attendance_policy, start_date=sub.start_date, end_date=sub.end_date,
        attended=attended, missed=missed, cancelled=cancelled,
        total_expected=total_expected, can_miss=can_miss
    )

@router.post("/subjects", response_model=schemas.SubjectDashboardResponse)
def create_subject(payload: schemas.SubjectCreate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if payload.end_date < payload.start_date:
        raise HTTPException(status_code=400, detail="End date must be after start date.")
    
    new_sub = models.Subject(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        name=payload.name,
        code=payload.code,
        attendance_policy=payload.attendance_policy,
        start_date=payload.start_date,
        end_date=payload.end_date
    )
    db.add(new_sub)
    db.commit()
    db.refresh(new_sub)
    
    return get_subject_dashboard_metrics(new_sub, current_user.id, db)

@router.get("/subjects", response_model=List[schemas.SubjectDashboardResponse])
def get_subjects(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    subjects = db.query(models.Subject).filter(models.Subject.user_id == current_user.id).order_by(models.Subject.created_at.desc()).all()
    result = [get_subject_dashboard_metrics(sub, current_user.id, db) for sub in subjects]
    return result

@router.patch("/subjects/{subject_id}", response_model=schemas.SubjectDashboardResponse)
def update_subject(subject_id: str, payload: schemas.SubjectUpdate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    subject = db.query(models.Subject).filter(models.Subject.id == subject_id, models.Subject.user_id == current_user.id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
        
    if payload.name is not None: subject.name = payload.name
    if payload.code is not None: subject.code = payload.code
    if payload.attendance_policy is not None: subject.attendance_policy = payload.attendance_policy
    if payload.start_date is not None: subject.start_date = payload.start_date
    if payload.end_date is not None: subject.end_date = payload.end_date
    
    if subject.end_date < subject.start_date:
        raise HTTPException(status_code=400, detail="End date must be after start date.")
        
    db.commit()
    db.refresh(subject)
    
    return get_subject_dashboard_metrics(subject, current_user.id, db)

@router.delete("/subjects/{subject_id}")
def delete_subject(subject_id: str, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    subject = db.query(models.Subject).filter(models.Subject.id == subject_id, models.Subject.user_id == current_user.id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
        
    db.delete(subject)
    db.commit()
    return {"success": True, "message": "Subject deleted successfully"}

@router.post("/events", response_model=schemas.TimetableEventResponse)
def create_event(payload: schemas.TimetableEventCreate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    subject = db.query(models.Subject).filter(models.Subject.id == payload.subject_id, models.Subject.user_id == current_user.id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
        
    new_event = models.TimetableEvent(
        id=str(uuid.uuid4()), user_id=current_user.id, subject_id=payload.subject_id,
        title=payload.title, location=payload.location, type=payload.type,
        day_of_week=payload.day_of_week, start_time=payload.start_time, end_time=payload.end_time
    )
    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    return new_event

@router.get("/events", response_model=List[schemas.TimetableEventResponse])
def get_events(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(models.TimetableEvent).filter(models.TimetableEvent.user_id == current_user.id).all()

@router.delete("/events/{event_id}")
def delete_event(event_id: str, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    event = db.query(models.TimetableEvent).filter(models.TimetableEvent.id == event_id, models.TimetableEvent.user_id == current_user.id).first()
    if event:
        db.delete(event)
        db.commit()
    return {"success": True}

@router.post("/attendance")
def mark_attendance(payload: schemas.AttendanceMark, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    event = db.query(models.TimetableEvent).filter(models.TimetableEvent.id == payload.event_id, models.TimetableEvent.user_id == current_user.id).first()
    if not event: raise HTTPException(status_code=404, detail="Event not found")

    record = db.query(models.AttendanceRecord).filter(
        models.AttendanceRecord.event_id == payload.event_id,
        models.AttendanceRecord.user_id == current_user.id,
        models.AttendanceRecord.date == payload.date
    ).first()

    if record:
        record.status = payload.status
    else:
        record = models.AttendanceRecord(
            id=str(uuid.uuid4()), event_id=payload.event_id, user_id=current_user.id,
            date=payload.date, status=payload.status
        )
        db.add(record)
    db.commit()
    return {"success": True}

@router.get("/attendance/subject/{subject_id}", response_model=List[schemas.AttendanceRecordResponse])
def get_attendance_history(subject_id: str, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    records = db.query(models.AttendanceRecord).join(models.TimetableEvent).join(models.Subject).filter(
        models.TimetableEvent.subject_id == subject_id,
        models.AttendanceRecord.user_id == current_user.id
    ).order_by(models.AttendanceRecord.date.desc()).all()
    
    return [schemas.AttendanceRecordResponse(
        id=r.id, event_id=r.event_id, date=r.date, status=r.status,
        event_title=r.event.title, event_type=r.event.type, subject_name=r.event.subject.name
    ) for r in records]

@router.delete("/attendance/{record_id}")
def delete_attendance(record_id: str, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    record = db.query(models.AttendanceRecord).filter(models.AttendanceRecord.id == record_id, models.AttendanceRecord.user_id == current_user.id).first()
    if record:
        db.delete(record)
        db.commit()
    return {"success": True}