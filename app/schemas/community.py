from pydantic import BaseModel
from app.enum.enum import UserRole

class MemberUpdateRoleRequest(BaseModel):
    role: UserRole

class MemberBlockRequest(BaseModel):
    is_blocked: bool