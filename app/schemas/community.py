from pydantic import BaseModel
from app.enum.enum import UserRole

class MemberUpdateRoleRequest(BaseModel):
    role: UserRole

class MemberBlockRequest(BaseModel):
    is_blocked: bool

class RollNumberUpdateRequest(BaseModel):
    roll_number: str

class AutoRollNumberRequest(BaseModel):
    extract_roll_from_email: bool