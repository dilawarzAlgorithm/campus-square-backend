from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from app.enum.enum import HubPrivacy

class HubCreate(BaseModel):
    name: str
    description: str
    type: str # 'CLUB', 'STUDY_GROUP', or 'TEAM'
    privacy: HubPrivacy
    avatar_url: Optional[str] = None
    parent_id: Optional[str] = None

class HubResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    type: str
    privacy: HubPrivacy
    avatar_url: Optional[str] = None
    member_count: int = 0
    is_member: bool = False
    is_admin: bool = False
    is_lead: bool = False
    is_pending: bool = False
    parent_id: Optional[str] = None
    is_saved: bool = False
    created_at: datetime

    class Config:
        from_attributes = True