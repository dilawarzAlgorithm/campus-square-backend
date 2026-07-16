from typing import Optional
from pydantic import BaseModel, EmailStr, Field

from app.enum.enum import UserRole

class ProfileSchema(BaseModel):
    dietary_preference: Optional[str] = None
    sleep_schedule: Optional[str] = None
    study_habits: Optional[str] = None

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    first_name: str
    last_name: str
    role: UserRole
    is_verified: bool
    is_blocked: bool
    requires_password_change: bool = False
    karma: int
    institution_id: str
    profile: Optional[ProfileSchema] = None

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
    
    institution_name: Optional[str] = None
    institution_short_name: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    institution_name: Optional[str] = None
    institution_short_name: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8)


class ChangePasswordResponse(BaseModel):
    success: bool
    message: str
    user: UserResponse


class ResendOtp(BaseModel):
    email: EmailStr
    password: str

class OTPVerificationRequest(BaseModel):
    email: EmailStr
    otp: str