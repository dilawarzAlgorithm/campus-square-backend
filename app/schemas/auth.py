from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from app.enum.enum import UserRole
from datetime import datetime

class ProfileSchema(BaseModel):
    dietary_preference: Optional[str] = None
    sleep_schedule: Optional[str] = None
    study_habits: Optional[str] = None
    class Config:
        from_attributes = True

class KarmaTierInfo(BaseModel):
    level: int
    title: str
    next_tier_title: Optional[str] = None
    points_to_next: Optional[int] = None
    progress_percentage: float

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    first_name: str
    last_name: str
    role: UserRole
    roll_number: Optional[str] = None
    is_verified: bool
    is_blocked: bool
    requires_password_change: bool = False
    karma: int
    institution_id: Optional[str] = None
    institution_name: Optional[str] = None
    department_id: Optional[str] = None
    department_name: Optional[str] = None
    profile: Optional[ProfileSchema] = None
    karma_tier: Optional[KarmaTierInfo] = None
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user: UserResponse

class TokenData(BaseModel):
    email: EmailStr

class TokenRefreshRequest(BaseModel):
    refresh_token: str

class TokenRefreshResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters long")
    first_name: str
    last_name: str
    requested_role: UserRole = UserRole.STUDENT
    department_id: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8)

class ChangePasswordResponse(BaseModel):
    success: bool
    message: str
    user: UserResponse

class UpdateNameRequest(BaseModel):
    first_name: str
    last_name: str
    
class UpdateProfileRequest(BaseModel):
    dietary_preference: Optional[str] = None
    sleep_schedule: Optional[str] = None
    study_habits: Optional[str] = None

class ResendOtp(BaseModel):
    email: EmailStr
    password: str

class OTPVerificationRequest(BaseModel):
    email: EmailStr
    otp: str

class InstitutionCreateRequest(BaseModel):
    name: str = Field(..., description="Full name of the institution")
    short_name: str = Field(..., description="Short name or acronym")
    domain: str = Field(..., description="Email domain for the institution (e.g., mit.edu)")
    head_email: EmailStr = Field(..., description="Email of the assigned Community Head")
    head_first_name: str = Field(..., description="First name of the Community Head")
    head_last_name: str = Field(..., description="Last name of the Community Head")
    head_password: str = Field(..., min_length=8, description="Initial password for the Community Head")

class InstitutionResponse(BaseModel):
    id: str
    name: str
    short_name: str
    domain: str
    extract_roll_from_email: bool
    created_at: datetime
    updated_at: datetime
    is_blocked: bool = False

    class Config:
        from_attributes = True