from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database.database import get_db
from app.models import models
from app.schemas import schemas
from app.core.auth.oauth2 import get_current_user
from app.enum.enum import UserRole

router = APIRouter(
    prefix="/api/community",
    tags=["Community Management"]
)

def require_community_head(current_user: models.User = Depends(get_current_user)):
    if current_user.role not in [UserRole.COMMUNITY_HEAD, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Not authorized to perform community management actions."
        )
    return current_user

@router.get("/members", response_model=List[schemas.UserResponse])
def get_community_members(
    current_user: models.User = Depends(require_community_head),
    db: Session = Depends(get_db)
):
    members = db.query(models.User).filter(
        models.User.institution_id == current_user.institution_id,
        models.User.role != UserRole.ADMIN
    ).order_by(models.User.first_name.asc()).all()
    
    return members

@router.patch("/members/{user_id}/role", response_model=schemas.UserResponse)
def update_member_role(
    user_id: str,
    payload: schemas.MemberUpdateRoleRequest,
    current_user: models.User = Depends(require_community_head),
    db: Session = Depends(get_db)
):
    target_user = db.query(models.User).filter(
        models.User.id == user_id,
        models.User.institution_id == current_user.institution_id
    ).first()
    
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found in your community.")
        
    if target_user.role == UserRole.COMMUNITY_HEAD:
        raise HTTPException(status_code=400, detail="Cannot modify another Community Head.")
        
    target_user.role = payload.role
    db.commit()
    db.refresh(target_user)
    return target_user

@router.patch("/members/{user_id}/block", response_model=schemas.UserResponse)
def block_member(
    user_id: str,
    payload: schemas.MemberBlockRequest,
    current_user: models.User = Depends(require_community_head),
    db: Session = Depends(get_db)
):
    target_user = db.query(models.User).filter(
        models.User.id == user_id,
        models.User.institution_id == current_user.institution_id
    ).first()
    
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found in your community.")
        
    if target_user.role == UserRole.COMMUNITY_HEAD:
        raise HTTPException(status_code=400, detail="Cannot block another Community Head.")
        
    target_user.is_blocked = payload.is_blocked
    db.commit()
    db.refresh(target_user)
    return target_user