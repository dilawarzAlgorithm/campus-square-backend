import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database.database import get_db
from app.models import models
from app.schemas import schemas
from app.core.auth.oauth2 import get_current_user
from app.enum.enum import UserRole
from app.core.features.utils import hash

router = APIRouter(
    prefix="/api/admin",
    tags=["Global Administration"]
)

def require_admin(current_user: models.User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Not authorized. Global admin privileges required."
        )
    return current_user

@router.get("/metrics")
def get_global_metrics(current_user: models.User = Depends(require_admin), db: Session = Depends(get_db)):
    total_institutions = db.query(models.Institution).count()
    total_users = db.query(models.User).count()
    total_heads = db.query(models.User).filter(models.User.role == UserRole.COMMUNITY_HEAD).count()
    total_resources = db.query(models.AcademicResource).count()
    
    return {
        "total_institutions": total_institutions,
        "total_users": total_users,
        "total_heads": total_heads,
        "total_resources": total_resources
    }

@router.get("/institutions", response_model=List[schemas.InstitutionResponse])
def get_all_institutions(current_user: models.User = Depends(require_admin), db: Session = Depends(get_db)):
    return db.query(models.Institution).order_by(models.Institution.name.asc()).all()

@router.post("/institutions", response_model=schemas.InstitutionResponse, status_code=status.HTTP_201_CREATED)
def add_institution_and_head(
    payload: schemas.InstitutionCreateRequest, 
    current_user: models.User = Depends(require_admin), 
    db: Session = Depends(get_db)
):
    payload.domain = payload.domain.lower()
    payload.head_email = payload.head_email.lower()

    if db.query(models.Institution).filter(models.Institution.domain == payload.domain).first():
        raise HTTPException(status_code=400, detail="An institution with this domain already exists.")
        
    if db.query(models.User).filter(models.User.email == payload.head_email).first():
        raise HTTPException(status_code=400, detail="A user with the specified head email already exists.")

    new_inst = models.Institution(
        id=str(uuid.uuid4()),
        name=payload.name,
        short_name=payload.short_name,
        domain=payload.domain
    )
    db.add(new_inst)
    db.flush()

    head_user = models.User(
        id=str(uuid.uuid4()),
        email=payload.head_email,
        password_hash=hash(payload.head_password),
        first_name=payload.head_first_name,
        last_name=payload.head_last_name,
        role=UserRole.COMMUNITY_HEAD,
        institution_id=new_inst.id,
        is_verified=True, 
        requires_password_change=True
    )
    db.add(head_user)
    
    new_profile = models.Profile(id=str(uuid.uuid4()), user_id=head_user.id)
    db.add(new_profile)

    db.commit()
    db.refresh(new_inst)
    
    return new_inst

@router.get("/users", response_model=List[schemas.UserResponse])
def get_all_users(current_user: models.User = Depends(require_admin), db: Session = Depends(get_db)):
    return db.query(models.User).order_by(models.User.created_at.desc()).all()

@router.patch("/users/{user_id}/block", response_model=schemas.UserResponse)
def toggle_user_block(
    user_id: str, 
    payload: schemas.MemberBlockRequest,
    current_user: models.User = Depends(require_admin), 
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
        
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot block yourself.")

    user.is_blocked = payload.is_blocked
    db.commit()
    db.refresh(user)
    return user