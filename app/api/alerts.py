import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database.database import get_db, SessionLocal
from app.models import models
from app.schemas.square import AlertCreate, AlertResponse
from app.core.auth.oauth2 import get_current_user
from app.api.notification import trigger_push_notification
from app.enum.enum import UserRole

router = APIRouter(
    prefix="/api/alerts",
    tags=["Anonymous Campus Alerts"]
)

def bulk_save_in_app_notifications(institution_id: str, alert_id: str, message: str):
    db = SessionLocal()
    try:
        if hasattr(models, 'Notification'):
            users = db.query(models.User.id).filter(
                models.User.institution_id == institution_id,
                models.User.is_blocked == False
            ).all()
            
            notifications = []
            for (user_id,) in users:
                notifications.append(
                    models.Notification(
                        id=str(uuid.uuid4()),
                        recipient_id=user_id,
                        title="🚨 Campus Alert",
                        body=message,
                        type="ANONYMOUS_ALERT",
                        related_entity_id=alert_id
                    )
                )
            
            if notifications:
                db.bulk_save_objects(notifications)
                db.commit()
    except Exception as e:
        print(f"Failed to create in-app notifications for alert: {e}")
    finally:
        db.close()

@router.post("", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
def create_anonymous_alert(
    payload: AlertCreate, 
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    
    if not current_user.can_send_alerts:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Your access to the emergency alert system has been suspended by the administration."
        )

    new_alert = models.Alert(
        id=str(uuid.uuid4()),
        message=payload.message.strip(),
        sender_id=current_user.id,
        institution_id=current_user.institution_id
    )
    db.add(new_alert)
    db.commit()
    db.refresh(new_alert)

    topic = f"{current_user.institution_id}_urgent_alerts"
    background_tasks.add_task(
        trigger_push_notification,
        title="🚨 Campus Alert",
        body=new_alert.message,
        topic=topic,
        data_payload={"alert_id": new_alert.id, "type": "anonymous_alert"}
    )
    
    background_tasks.add_task(
        bulk_save_in_app_notifications,
        institution_id=current_user.institution_id,
        alert_id=new_alert.id,
        message=new_alert.message
    )
    
    return new_alert

@router.get("", response_model=List[AlertResponse])
def get_recent_alerts(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(models.Alert).filter(
        models.Alert.institution_id == current_user.institution_id,
        models.Alert.is_active == True
    ).order_by(models.Alert.created_at.desc()).limit(30).all()


@router.post("/{alert_id}/block-sender")
def block_alert_sender(
    alert_id: str, 
    current_user: models.User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    if current_user.role not in [UserRole.ADMIN, UserRole.COMMUNITY_HEAD]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only administration can block alert abusers.")

    alert = db.query(models.Alert).filter(
        models.Alert.id == alert_id,
        models.Alert.institution_id == current_user.institution_id
    ).first()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found.")

    sender = db.query(models.User).filter(models.User.id == alert.sender_id).first()
    if sender:
        sender.can_send_alerts = False
        alert.is_active = False
        db.commit()

    return {
        "success": True, 
        "message": "The sender of this alert has been permanently blocked from using the alert system, and the alert was removed."
    }