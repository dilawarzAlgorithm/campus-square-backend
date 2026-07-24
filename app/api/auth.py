import secrets
import uuid
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database.database import get_db
from app.models import models
from app.schemas import schemas
from app.enum.enum import UserRole
from app.core.config.config import settings
from app.core.features.utils import hash, verify, extract_domain, generate_otp, calculate_karma_tier
from app.core.auth.oauth2 import create_access_token, REFRESH_TOKEN_EXPIRE_DAYS
from app.core.features.mail import send_otp_email
from app.core.auth.oauth2 import get_current_user
from app.schemas.vault import DepartmentResponse

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)

@router.get("/departments-by-email", response_model=list[DepartmentResponse])
def get_departments_by_email(email: str, db: Session = Depends(get_db)):
    email = email.lower()
    try:
        domain = extract_domain(email)
    except ValueError:
        return []
        
    institution = db.query(models.Institution).filter(models.Institution.domain == domain).first()
    if not institution:
        return []
        
    return db.query(models.Department).filter(models.Department.institution_id == institution.id).order_by(models.Department.name.asc()).all()

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: schemas.RegisterRequest, background_task: BackgroundTasks , db: Session = Depends(get_db)):
    payload.email = payload.email.lower()
    
    try:
        domain = extract_domain(payload.email)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Invalid email format."
        )

    existing_user = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address is already registered."
        )

    institution = db.query(models.Institution).filter(models.Institution.domain == domain).first()
    if not institution:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Your institution ({domain}) is not yet registered on Campus Square. Please contact your administrator."
        )

    if not payload.department_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A department selection is required. If your institution has no departments, please contact your Community Head to create one."
        )

    dept = db.query(models.Department).filter(
        models.Department.id == payload.department_id,
        models.Department.institution_id == institution.id
    ).first()

    if not dept:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid department selected."
        )

    roll_number = None
    if institution.extract_roll_from_email and payload.requested_role == UserRole.STUDENT:
        roll_number = payload.email.split('@')[0].upper()

    otp = generate_otp()
    user_id = str(uuid.uuid4())
    new_user = models.User(
        id=user_id,
        email=payload.email,
        password_hash=hash(payload.password),
        first_name=payload.first_name,
        last_name=payload.last_name,
        roll_number=roll_number,
        role=payload.requested_role,
        institution_id=institution.id,
        department_id=payload.department_id,
        is_verified=False,
        verification_otp=otp,
        otp_expires_at=datetime.now(timezone.utc) + timedelta(minutes=15)
    )

    db.add(new_user)
    db.flush()

    new_profile = models.Profile(
        id=str(uuid.uuid4()),
        user_id=user_id
    )
    db.add(new_profile)
    db.commit()

    background_task.add_task(send_otp_email, payload.email, otp, payload.first_name)

    return {
        "success": True,
        "message": f"Successfully registered! Please verify your email using the OTP sent to {payload.email}.",
        "user_id": new_user.id
    }

@router.post("/verify-otp")
def verify_otp(payload: schemas.OTPVerificationRequest, db: Session = Depends(get_db)):
    payload.email = payload.email.lower()
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    
    if user.is_verified:
        return {"message": "Email is already verified."}

    if user.verification_otp != payload.otp:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP code.")
    
    if datetime.now(timezone.utc) > user.otp_expires_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP has expired.")

    user.is_verified = True
    user.verification_otp = None
    user.otp_expires_at = None

    if user.department_id:
        dept_conv = db.query(models.Conversation).filter(
            models.Conversation.department_id == user.department_id,
            models.Conversation.type == "DEPARTMENT"
        ).first()
        
        if dept_conv:
            existing = db.query(models.ConversationParticipant).filter(
                models.ConversationParticipant.conversation_id == dept_conv.id,
                models.ConversationParticipant.user_id == user.id
            ).first()
            
            if not existing:
                p = models.ConversationParticipant(
                    id=str(uuid.uuid4()),
                    conversation_id=dept_conv.id,
                    user_id=user.id
                )
                db.add(p)

    db.commit()
    return {"success": True, "message": "Your account has been successfully verified! You can now log in."}

@router.post("/resend-otp")
def resend_otp(payload: schemas.ResendOtp, background_task: BackgroundTasks, db: Session = Depends(get_db)):
    payload.email = payload.email.lower()
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not verify(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password."
    )
    
    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is already verified. You can log in directly."
        )

    otp = generate_otp()
    user.verification_otp = otp
    user.otp_expires_at=datetime.now(timezone.utc) + timedelta(minutes=15)
    db.commit()
    db.refresh(user)
    
    background_task.add_task(send_otp_email, user.email, otp, user.first_name)
    return {"success": True, "message": "A new verification code has been sent."}

@router.post("/login", response_model=schemas.Token)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    payload.email = payload.email.lower()
    user = db.query(models.User).filter(models.User.email == payload.email).first()

    if not user or not verify(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password."
        )
        
    if user.is_blocked:
        raise HTTPException(status_code=403, detail="Your account has been blocked by the community head.")
        
    if user.role in [UserRole.ADMIN, UserRole.COMMUNITY_HEAD]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff and administrators must log in through the Staff Portal."
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account email is not verified yet. Please check your inbox for verification instructions."
        )

    access_token = create_access_token(data={"sub": user.email})
    refresh_token_str = secrets.token_urlsafe(64)
    refresh_expires = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    db_refresh_token = models.RefreshToken(
        id=str(uuid.uuid4()),
        token=refresh_token_str,
        user_id=user.id,
        expires_at=refresh_expires
    )
    db.add(db_refresh_token)
    db.commit()

    karma_info = calculate_karma_tier(user.karma)
    user_response = schemas.UserResponse.model_validate(user)
    user_response.karma_tier = karma_info

    return {
        "access_token": access_token,
        "refresh_token": refresh_token_str,
        "token_type": "bearer",
        "user": user_response
    }

def create_initial_admin(db: Session):
    admin_user = db.query(models.User).filter(models.User.email == settings.admin_id.lower()).first()
    if not admin_user:
        sys_inst = db.query(models.Institution).filter(models.Institution.domain == "system.local").first()
        if not sys_inst:
            sys_inst = models.Institution(
                id=str(uuid.uuid4()),
                name="System Administration",
                short_name="SYSTEM",
                domain="system.local"
            )
            db.add(sys_inst)
            db.flush()

        admin_user = models.User(
            id=str(uuid.uuid4()),
            email=settings.admin_id.lower(),
            password_hash=hash(settings.admin_password),
            first_name="Global",
            last_name="Admin",
            role=UserRole.ADMIN,
            institution_id=sys_inst.id,
            is_verified=True, 
            requires_password_change=True
        )
        db.add(admin_user)
        db.flush()
        
        new_profile = models.Profile(id=str(uuid.uuid4()), user_id=admin_user.id)
        db.add(new_profile)
        db.commit()
    return admin_user

@router.post("/login-staff")
def login_staff(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    payload.email = payload.email.lower()
    if payload.email == settings.admin_id.lower():
        create_initial_admin(db)

    user = db.query(models.User).filter(models.User.email == payload.email).first()

    if not user or not verify(payload.password, user.password_hash):
         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password.")
         
    if user.role not in [UserRole.ADMIN, UserRole.COMMUNITY_HEAD]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied. Not a staff member.")

    access_token = create_access_token(data={"sub": user.email})
    refresh_token_str = secrets.token_urlsafe(64)
    refresh_expires = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    db_refresh_token = models.RefreshToken(
        id=str(uuid.uuid4()),
        token=refresh_token_str,
        user_id=user.id,
        expires_at=refresh_expires
    )
    db.add(db_refresh_token)
    db.commit()

    karma_info = calculate_karma_tier(user.karma)
    user_response = schemas.UserResponse.model_validate(user)
    user_response.karma_tier = karma_info

    return {
        "access_token": access_token,
        "refresh_token": refresh_token_str,
        "token_type": "bearer",
        "user": user_response
    }


@router.post("/change-password")
def change_password(payload: schemas.ChangePasswordRequest, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not verify(payload.old_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect old password.")
    
    if verify(payload.new_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Old and same passwords can't be same.")
        
    current_user.password_hash = hash(payload.new_password)
    current_user.requires_password_change = False
    db.commit()
    db.refresh(current_user)

    karma_info = calculate_karma_tier(current_user.karma)
    user_response = schemas.UserResponse.model_validate(current_user)
    user_response.karma_tier = karma_info

    return {
        "success": True, 
        "message": "Password updated successfully.",
        "user": user_response
    }

@router.get("/me", response_model=schemas.UserResponse)
def get_me(current_user: models.User = Depends(get_current_user)):
    karma_info = calculate_karma_tier(current_user.karma)
    user_response = schemas.UserResponse.model_validate(current_user)
    user_response.karma_tier = karma_info
    return user_response

@router.patch("/name", response_model=schemas.UserResponse)
def update_name(payload: schemas.UpdateNameRequest, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    current_user.first_name = payload.first_name.strip()
    current_user.last_name = payload.last_name.strip()

    db.commit()
    db.refresh(current_user)
    
    karma_info = calculate_karma_tier(current_user.karma)
    user_response = schemas.UserResponse.model_validate(current_user)
    user_response.karma_tier = karma_info
    return user_response

@router.patch("/profile", response_model=schemas.UserResponse)
def update_profile(payload: schemas.UpdateProfileRequest, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    import uuid
    if not current_user.profile:
        new_profile = models.Profile(id=str(uuid.uuid4()), user_id=current_user.id)
        db.add(new_profile)
        db.flush()
        current_user.profile = new_profile

    if payload.dietary_preference is not None:
        current_user.profile.dietary_preference = payload.dietary_preference.strip()
    if payload.sleep_schedule is not None:
        current_user.profile.sleep_schedule = payload.sleep_schedule.strip()
    if payload.study_habits is not None:
        current_user.profile.study_habits = payload.study_habits.strip()

    db.commit()
    db.refresh(current_user)
    
    karma_info = calculate_karma_tier(current_user.karma)
    user_response = schemas.UserResponse.model_validate(current_user)
    user_response.karma_tier = karma_info
    return user_response

@router.post("/refresh", response_model=schemas.TokenRefreshResponse)
def refresh(payload: schemas.TokenRefreshRequest, db: Session = Depends(get_db)):
    db_token = db.query(models.RefreshToken).filter(
        models.RefreshToken.token == payload.refresh_token,
        models.RefreshToken.revoked == False
    ).first()

    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked refresh token."
        )

    if datetime.now(timezone.utc) > db_token.expires_at:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired. Please log in again."
        )

    user = db.query(models.User).filter(models.User.id == db_token.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found."
        )

    db_token.revoked = True

    new_refresh_token_str = secrets.token_urlsafe(64)
    new_refresh_expires = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    new_db_token = models.RefreshToken(
        id=str(uuid.uuid4()),
        token=new_refresh_token_str,
        user_id=user.id,
        expires_at=new_refresh_expires
    )
    db.add(new_db_token)

    new_access_token = create_access_token(data={"sub": user.email})

    db.commit()

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token_str,
        "token_type": "bearer"
    }