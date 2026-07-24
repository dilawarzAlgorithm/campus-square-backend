from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class ChatUser(BaseModel):
    id: str
    first_name: str
    last_name: str
    role: str
    is_online: Optional[bool] = False
    last_seen: Optional[datetime] = None

    class Config:
        from_attributes = True

class MessageReplyInfo(BaseModel):
    id: str
    content: str
    sender: ChatUser

    class Config:
        from_attributes = True

class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    content: str
    created_at: datetime
    sender: ChatUser
    reply_to: Optional[MessageReplyInfo] = None
    is_delivered: Optional[bool] = False
    is_read: Optional[bool] = False
    is_deleted: Optional[bool] = False
    is_edited: Optional[bool] = False

    class Config:
        from_attributes = True

class ConversationParticipantResponse(BaseModel):
    user: ChatUser

    class Config:
        from_attributes = True

class ConversationResponse(BaseModel):
    id: str
    type: str
    name: Optional[str] = None
    created_at: datetime
    participants: List[ConversationParticipantResponse]
    last_message: Optional[MessageResponse] = None
    unread_count: int = 0

    class Config:
        from_attributes = True

class ConversationParticipantResponse(BaseModel):
    user: ChatUser

    class Config:
        from_attributes = True
