from app.schemas.auth import (
    ProfileSchema,
    UserResponse,
    Token,
    TokenData,
    TokenRefreshRequest,
    TokenRefreshResponse,
    RegisterRequest,
    LoginRequest,
    OTPVerificationRequest,
    ChangePasswordRequest,
    ChangePasswordResponse,
    UpdateNameRequest,
    ResendOtp
)

from app.schemas.vault import (
    DepartmentCreate,
    DepartmentResponse,
    ResourceCreate,
    ResourceResponse,
    VoteRequest
)

from app.schemas.community import (
    MemberUpdateRoleRequest,
    MemberBlockRequest
)