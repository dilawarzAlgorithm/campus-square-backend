from typing import Optional
from pydantic import BaseModel, Field

from app.enum.enum import ResourceType, VoteType

class DepartmentCreate(BaseModel):
    name: str = Field(..., description="Full name of department, e.g. Computer Science")
    code: str = Field(..., description="Shorthand code identifier, e.g. CSE")

class DepartmentResponse(BaseModel):
    id: str
    name: str
    code: str
    institution_id: str

    class Config:
        from_attributes = True

class ResourceCreate(BaseModel):
    title: str = Field(..., min_length=3, description="E.g. Discrete Math PYQ 2024")
    description: Optional[str] = None
    file_url: str = Field(..., description="Secure cloud drive or file link to resource asset")
    resource_type: ResourceType = ResourceType.NOTE
    semester: int = Field(..., ge=1, le=8, description="Academic semester value ranging from 1 to 8")
    department_id: str

class ResourceResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    file_url: str
    resource_type: ResourceType
    semester: int
    upvote_count: int
    downvote_count: int
    department_id: str
    uploader_id: str

    class Config:
        from_attributes = True

class VoteRequest(BaseModel):
    vote_type: VoteType