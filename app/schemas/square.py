from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from app.enum.enum import SquareCategory, UserRole, VoteType
from app.schemas.auth import ProfileSchema

class VoteRequest(BaseModel):
    vote_type: VoteType

class NoticeAuthor(BaseModel):
    id: str
    first_name: str
    last_name: str
    role: UserRole
    profile: Optional[ProfileSchema] = None

    class Config:
        from_attributes = True

class CommentCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=500)
    parent_id: Optional[str] = None

class CommentResponse(BaseModel):
    id: str
    text: str
    created_at: datetime
    author: NoticeAuthor
    parent_id: Optional[str] = None

    class Config:
        from_attributes = True

class NestedCommentResponse(CommentResponse):
    replies: List['NestedCommentResponse'] = []

class NoticeCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=100)
    body: str = Field(..., min_length=10, description="Post details must be at least 10 characters long.")
    category: SquareCategory = SquareCategory.NOTICE
    urgent_until: Optional[datetime] = None
    image_url: Optional[str] = None
    file_url: Optional[str] = None

class NoticeResponse(BaseModel):
    id: str
    title: str
    body: str
    category: SquareCategory
    urgent_until: Optional[datetime]
    image_url: Optional[str]
    file_url: Optional[str]
    upvote_count: int = 0
    downvote_count: int = 0
    my_vote: Optional[VoteType] = None
    created_at: datetime
    updated_at: datetime
    author: NoticeAuthor
    comments: List[NestedCommentResponse] = []

    class Config:
        from_attributes = True