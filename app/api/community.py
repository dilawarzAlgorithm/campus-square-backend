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

@router.patch("/members/{user_id}/roll-number", response_model=schemas.UserResponse)
def update_roll_number(
    user_id: str,
    payload: schemas.RollNumberUpdateRequest,
    current_user: models.User = Depends(require_community_head),
    db: Session = Depends(get_db)
):
    target_user = db.query(models.User).filter(
        models.User.id == user_id,
        models.User.institution_id == current_user.institution_id
    ).first()
    
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found in your community.")
        
    target_user.roll_number = payload.roll_number.strip().upper()
    db.commit()
    db.refresh(target_user)
    return target_user

@router.post("/settings/auto-roll-numbers", status_code=status.HTTP_200_OK)
def trigger_auto_roll_numbers(
    payload: schemas.AutoRollNumberRequest,
    current_user: models.User = Depends(require_community_head),
    db: Session = Depends(get_db)
):
    institution = db.query(models.Institution).filter(models.Institution.id == current_user.institution_id).first()
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found.")
        
    institution.extract_roll_from_email = payload.extract_roll_from_email
    
    updated_count = 0
    if payload.extract_roll_from_email:
        students = db.query(models.User).filter(
            models.User.institution_id == current_user.institution_id,
            models.User.role == UserRole.STUDENT,
            models.User.roll_number == None
        ).all()
        
        for student in students:
            student.roll_number = student.email.split('@')[0].upper()
            updated_count += 1
            
    db.commit()
    
    return {
        "success": True, 
        "message": f"Settings saved. Auto-assigned roll numbers to {updated_count} students.",
        "extract_roll_from_email": institution.extract_roll_from_email
    }