import secrets
import uuid
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database.database import get_db
from app.models import models
from app.schemas import schemas
from app.core.features.utils import hash, verify, extract_domain, generate_otp
from app.core.auth.oauth2 import create_access_token, REFRESH_TOKEN_EXPIRE_DAYS
from app.core.features.mail import send_otp_email

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: schemas.RegisterRequest, background_task: BackgroundTasks , db: Session = Depends(get_db)):
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

    # Check or dynamically create the Institution (Bottom-Up Model)
    institution = db.query(models.Institution).filter(models.Institution.domain == domain).first()
    if not institution:
        if not payload.institution_name or not payload.institution_short_name:
            return {
                "requires_onboarding": True,
                "message": (
                    f"It looks like you are the first user registering from @{domain}! "
                    "To set up Campus Square for your campus, please provide the 'institution_name' and 'institution_short_name'."
                )
            }
        
        institution = models.Institution(
            id=str(uuid.uuid4()),
            name=payload.institution_name,
            short_name=payload.institution_short_name,
            domain=domain
        )
        db.add(institution)
        db.flush()

    otp = generate_otp()

    user_id = str(uuid.uuid4())
    new_user = models.User(
        id=user_id,
        email=payload.email,
        password_hash=hash(payload.password),
        first_name=payload.first_name,
        last_name=payload.last_name,
        role=payload.requested_role,
        institution_id=institution.id,
        is_verified=False,
        verification_otp=otp,
        otp_expires_at=datetime.now(timezone.utc) + timedelta(minutes=1)
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
    db.commit()

    return {"success": True, "message": "Your account has been successfully verified! You can now log in."}

@router.post("/resend-otp")
def resend_otp(payload: schemas.ResendOtp, background_task: BackgroundTasks, db: Session = Depends(get_db)):
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
    user.otp_expires_at=datetime.now(timezone.utc) + timedelta(minutes=1)
    db.commit()
    db.refresh(user)
    background_task.add_task(send_otp_email, user.email, otp, user.first_name)

    return {"success": True, "message": "A new verification code has been sent."}

@router.post("/login", response_model=schemas.Token)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not verify(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password."
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

    return {
        "access_token": access_token,
        "refresh_token": refresh_token_str,
        "token_type": "bearer",
        "user": user
    }


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