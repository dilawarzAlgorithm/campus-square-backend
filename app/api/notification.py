import firebase_admin
from firebase_admin import credentials, messaging
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
import os

from app.core.config.config import settings

router = APIRouter(
    prefix="/api/notifications",
    tags=["Push Notifications"]
)
FIREBASE_KEY_PATH = settings.firebase_admin_credentials

if not firebase_admin._apps:
    try:
        cred = credentials.Certificate(FIREBASE_KEY_PATH)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        print(f"Warning: Failed to initialize Firebase Admin SDK. Push notifications will fail. {e}")

class PushNotificationRequest(BaseModel):
    title: str
    body: str
    topic: str
    data_payload: dict = {}

@router.post("/send")
def send_push_notification(payload: PushNotificationRequest):
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=payload.title,
                body=payload.body,
            ),
            data=payload.data_payload,
            topic=payload.topic,
        )
        
        response = messaging.send(message)
        
        return {"success": True, "message_id": response}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send notification: {str(e)}"
        )

def trigger_push_notification(title: str, body: str, topic: str, data_payload: dict = None):
    if not firebase_admin._apps:
        print("Firebase not initialized. Skipping push notification.")
        return
        
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data_payload or {},
            topic=topic,
        )
        messaging.send(message)
    except Exception as e:
        print(f"Background Push Notification Error: {e}")
