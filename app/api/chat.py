import uuid
import json
from typing import List, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.core.database.database import get_db
from app.models import models
from app.schemas import schemas
from app.core.auth.oauth2 import get_current_user, verify_access_token

router = APIRouter(
    prefix="/api/chat",
    tags=["Chat & Messaging"]
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, conversation_id: str):
        await websocket.accept()
        if conversation_id not in self.active_connections:
            self.active_connections[conversation_id] = []
        self.active_connections[conversation_id].append(websocket)

    def disconnect(self, websocket: WebSocket, conversation_id: str):
        if conversation_id in self.active_connections:
            self.active_connections[conversation_id].remove(websocket)
            if not self.active_connections[conversation_id]:
                del self.active_connections[conversation_id]

    async def broadcast_to_conversation(self, conversation_id: str, message_data: dict):
        if conversation_id in self.active_connections:
            for connection in self.active_connections[conversation_id]:
                await connection.send_json(message_data)

manager = ConnectionManager()


@router.post("/dm/{target_user_id}", response_model=schemas.ConversationResponse)
def get_or_create_dm(
    target_user_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if target_user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot create a DM with yourself.")

    target_user = db.query(models.User).filter(models.User.id == target_user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Target user not found.")

    conversations = db.query(models.Conversation).join(models.ConversationParticipant).filter(
        models.Conversation.type == "DM",
        models.ConversationParticipant.user_id.in_([current_user.id, target_user_id])
    ).all()

    existing_conv = None
    for conv in conversations:
        participant_ids = [p.user_id for p in conv.participants]
        if set(participant_ids) == {current_user.id, target_user_id}:
            existing_conv = conv
            break

    if existing_conv:
        return existing_conv

    new_conv = models.Conversation(id=str(uuid.uuid4()), type="DM")
    db.add(new_conv)
    
    p1 = models.ConversationParticipant(id=str(uuid.uuid4()), conversation_id=new_conv.id, user_id=current_user.id)
    p2 = models.ConversationParticipant(id=str(uuid.uuid4()), conversation_id=new_conv.id, user_id=target_user_id)
    
    db.add(p1)
    db.add(p2)
    db.commit()
    db.refresh(new_conv)
    return new_conv

@router.get("/conversations", response_model=List[schemas.ConversationResponse])
def get_my_conversations(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    participants = db.query(models.ConversationParticipant).filter(
        models.ConversationParticipant.user_id == current_user.id
    ).all()
    
    conv_ids = [p.conversation_id for p in participants]
    
    conversations = db.query(models.Conversation).filter(
        models.Conversation.id.in_(conv_ids)
    ).order_by(models.Conversation.created_at.desc()).all()

    for conv in conversations:
        last_msg = db.query(models.Message).filter(
            models.Message.conversation_id == conv.id
        ).order_by(models.Message.created_at.desc()).first()
        conv.last_message = last_msg
        
        unread_count = db.query(models.Message).filter(
            models.Message.conversation_id == conv.id,
            models.Message.sender_id != current_user.id,
            models.Message.is_read == False
        ).count()
        conv.unread_count = unread_count

    conversations.sort(
        key=lambda c: c.last_message.created_at if c.last_message else c.created_at, 
        reverse=True
    )
    return conversations

@router.get("/unread-count")
def get_global_unread_count(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    participants = db.query(models.ConversationParticipant).filter(
        models.ConversationParticipant.user_id == current_user.id
    ).all()
    conv_ids = [p.conversation_id for p in participants]
    
    count = db.query(models.Message).filter(
        models.Message.conversation_id.in_(conv_ids),
        models.Message.sender_id != current_user.id,
        models.Message.is_read == False
    ).count()
    return {"unread_count": count}

@router.get("/conversations/{conversation_id}/messages", response_model=List[schemas.MessageResponse])
def get_messages(
    conversation_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    is_participant = db.query(models.ConversationParticipant).filter(
        models.ConversationParticipant.conversation_id == conversation_id,
        models.ConversationParticipant.user_id == current_user.id
    ).first()

    if not is_participant:
        raise HTTPException(status_code=403, detail="Not a participant in this conversation.")

    messages = db.query(models.Message).filter(
        models.Message.conversation_id == conversation_id
    ).order_by(models.Message.created_at.desc()).limit(50).all()
    
    return messages


@router.websocket("/ws/{conversation_id}")
async def websocket_chat(websocket: WebSocket, conversation_id: str, token: str, db: Session = Depends(get_db)):
    try:
        credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        token_data = verify_access_token(token, credentials_exception)
        user = db.query(models.User).filter(models.User.email == token_data.email).first()
        if not user or user.is_blocked:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    is_participant = db.query(models.ConversationParticipant).filter(
        models.ConversationParticipant.conversation_id == conversation_id,
        models.ConversationParticipant.user_id == user.id
    ).first()

    if not is_participant:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(websocket, conversation_id)

    try:
        while True:
            raw_data = await websocket.receive_text()
            try:
                payload = json.loads(raw_data)
                action = payload.get("type")
                
                if action == "message":
                    new_message = models.Message(
                        id=str(uuid.uuid4()),
                        conversation_id=conversation_id,
                        sender_id=user.id,
                        content=payload.get("content", ""),
                        reply_to_id=payload.get("reply_to_id")
                    )
                    db.add(new_message)
                    db.commit()
                    db.refresh(new_message)

                    reply_obj = None
                    if new_message.reply_to_id:
                        orig = db.query(models.Message).filter(models.Message.id == new_message.reply_to_id).first()
                        if orig:
                            reply_obj = {
                                "id": orig.id,
                                "content": orig.content,
                                "sender": {
                                    "id": orig.sender.id,
                                    "first_name": orig.sender.first_name,
                                    "last_name": orig.sender.last_name,
                                    "role": orig.sender.role.value
                                }
                            }

                    message_data = {
                        "type": "new_message",
                        "message": {
                            "id": new_message.id,
                            "conversation_id": new_message.conversation_id,
                            "content": new_message.content,
                            "created_at": new_message.created_at.isoformat(),
                            "is_read": new_message.is_read,
                            "is_deleted": new_message.is_deleted,
                            "reply_to": reply_obj,
                            "sender": {
                                "id": user.id,
                                "first_name": user.first_name,
                                "last_name": user.last_name,
                                "role": user.role.value
                            }
                        }
                    }
                    await manager.broadcast_to_conversation(conversation_id, message_data)
                    
                elif action == "typing":
                    await manager.broadcast_to_conversation(conversation_id, {
                        "type": "typing_status",
                        "user_id": user.id,
                        "is_typing": payload.get("is_typing", False)
                    })
                    
                elif action == "mark_read":
                    db.query(models.Message).filter(
                        models.Message.conversation_id == conversation_id,
                        models.Message.sender_id != user.id,
                        models.Message.is_read == False
                    ).update({"is_read": True})
                    db.commit()
                    
                    await manager.broadcast_to_conversation(conversation_id, {
                        "type": "messages_read",
                        "user_id": user.id
                    })
            except json.JSONDecodeError:
                pass # Ignore malformed data

    except WebSocketDisconnect:
        manager.disconnect(websocket, conversation_id)
        
@router.delete("/messages/{message_id}")
async def delete_message(
    message_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    msg = db.query(models.Message).filter(models.Message.id == message_id).first()
    if not msg: 
        raise HTTPException(status_code=404)
    if msg.sender_id != current_user.id: 
        raise HTTPException(status_code=403, detail="Not authorized to delete this message.")
    
    msg.is_deleted = True
    msg.content = "🚫 This message was deleted"
    db.commit()
    
    await manager.broadcast_to_conversation(msg.conversation_id, {
        "type": "message_deleted",
        "message_id": message_id
    })
    return {"success": True}