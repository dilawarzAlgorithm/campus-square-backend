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
    UpdateProfileRequest,
    ResendOtp,
    InstitutionCreateRequest,
    InstitutionResponse,
    KarmaTierInfo,
    FCMTokenUpdate,
    InstitutionStorageLimitRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    RecoveryEmailOtpRequest,
    VerifyRecoveryEmailRequest,
)

from app.schemas.vault import (
    DepartmentCreate,
    DepartmentResponse,
    ResourceCreate,
    ResourceUpdate,
    ResourceResponse,
    VoteRequest
)

from app.schemas.community import (
    MemberUpdateRoleRequest,
    MemberBlockRequest,
    RollNumberUpdateRequest,
    AutoRollNumberRequest,
    StorageLimitUpdateRequest
)

from app.schemas.square import (
    VoteRequest,
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

from app.schemas.notification import (
    PushNotificationRequest,
    BroadcastRequest
)

from app.schemas.bazaar import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductSeller
)

from app.schemas.config import (
    AppConfigResponse,
    AppConfigUpdate
)

from app.schemas.hub import (
    HubCreate,
    HubResponse
)