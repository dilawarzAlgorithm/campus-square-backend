import json
import firebase_admin
from firebase_admin import credentials, messaging
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
import os

from app.core.config.config import settings
from app.core.auth.oauth2 import get_current_user
from app.enum.enum import UserRole
from app.schemas import schemas

router = APIRouter(
    prefix="/api/notifications",
    tags=["Push Notifications"]
)
# FIREBASE_KEY_PATH = settings.firebase_admin_credentials

# if not firebase_admin._apps:
#     try:
#         cred = credentials.Certificate(FIREBASE_KEY_PATH)
#         firebase_admin.initialize_app(cred)
#     except Exception as e:
#         print(f"Warning: Failed to initialize Firebase Admin SDK. Push notifications will fail. {e}")

firebase_secret = settings.firebase_json_str

if not firebase_admin._apps:
    try:
        if firebase_secret:
            cred_dict = json.loads(firebase_secret)
            cred = credentials.Certificate(cred_dict)
        else:
            local_file = settings.firebase_admin_credentials
            if os.path.exists(local_file):
                cred = credentials.Certificate(local_file)
            else:
                raise FileNotFoundError(f"Local credential file {local_file} not found.")
            
        firebase_admin.initialize_app(cred)
        print("Firebase Admin SDK initialized successfully.")
    except Exception as e:
        print(f"Warning: Failed to initialize Firebase Admin SDK. Push notifications will fail. Error: {e}")

@router.post("/send")
def send_push_notification(payload: schemas.PushNotificationRequest):
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

@router.post("/broadcast")
def send_global_broadcast(payload: schemas.BroadcastRequest, current_user = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only administrators can send global broadcasts.")
    try:
        message = messaging.Message(
            notification=messaging.Notification(title=payload.title, body=payload.body),
            topic="all_users"
        )
        messaging.send(message)
        return {"success": True, "message": "Broadcast sent to all users."}
    except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send global notification: {str(e)}"
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

def send_token_push_notification(title: str, body: str, token: str, data_payload: dict = None):
    if not firebase_admin._apps or not token:
        return
    try:
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data=data_payload or {},
            token=token,
        )
        messaging.send(message)
    except Exception as e:
        print(f"Targeted Push Notification Error: {e}")