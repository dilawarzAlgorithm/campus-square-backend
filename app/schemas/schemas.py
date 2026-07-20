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

from app.schemas.square import (
    NoticeAuthor,
    CommentCreate,
    CommentResponse,
    NestedCommentResponse,
    NoticeCreate,
    NoticeResponse
)

from app.schemas.chat import (
    ChatUser,
    MessageResponse,
    ConversationParticipantResponse,
    ConversationResponse
)