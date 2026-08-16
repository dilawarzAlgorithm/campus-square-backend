from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database.database import get_db
from app.models import models
from app.schemas import schemas
from app.core.auth.oauth2 import get_current_user
from app.enum.enum import UserRole
from app.schemas.config import AppConfigUpdate, AppConfigResponse

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

@router.patch("/settings/campaign", response_model=AppConfigResponse)
def update_campaign(
    payload: AppConfigUpdate,
    current_user: models.User = Depends(require_community_head),
    db: Session = Depends(get_db)
):
    inst = db.query(models.Institution).filter(models.Institution.id == current_user.institution_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found.")
        
    if payload.version_id is not None: inst.campaign_version_id = payload.version_id
    if payload.show_popup is not None: inst.show_popup = payload.show_popup
    if payload.popup_title is not None: inst.popup_title = payload.popup_title
    if payload.popup_message is not None: inst.popup_message = payload.popup_message
    if payload.lottie_url is not None: inst.lottie_url = payload.lottie_url
    if payload.target_route is not None: inst.target_route = payload.target_route
    
    if payload.show_banner is not None: inst.show_banner = payload.show_banner
    if payload.banner_title is not None: inst.banner_title = payload.banner_title
    if payload.banner_message is not None: inst.banner_message = payload.banner_message
    if payload.banner_action_url is not None: inst.banner_action_url = payload.banner_action_url
    
    if payload.primary_color_hex is not None: 
        inst.primary_color_hex = payload.primary_color_hex if payload.primary_color_hex.strip() else None

    db.commit()
    db.refresh(inst)

    return AppConfigResponse(
        version_id=inst.campaign_version_id or "v1",
        show_popup=inst.show_popup or False,
        popup_title=inst.popup_title,
        popup_message=inst.popup_message,
        lottie_url=inst.lottie_url,
        target_route=inst.target_route,
        show_banner=inst.show_banner or False,
        banner_title=inst.banner_title,
        banner_message=inst.banner_message,
        banner_action_url=inst.banner_action_url,
        primary_color_hex=inst.primary_color_hex
    )

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
async def block_member(
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

    from app.api.chat import manager
    if payload.is_blocked:
        await manager.broadcast_to_user_hub(target_user.id, {"type": "account_blocked", "user_id": target_user.id})

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

@router.patch("/members/{user_id}/storage-limit", response_model=schemas.UserResponse)
def update_storage_limit(
    user_id: str,
    payload: schemas.StorageLimitUpdateRequest,
    current_user: models.User = Depends(require_community_head),
    db: Session = Depends(get_db)
):
    target_user = db.query(models.User).filter(
        models.User.id == user_id,
        models.User.institution_id == current_user.institution_id
    ).first()

    if not target_user:
        raise HTTPException(status_code=404, detail="User not found in your community.")

    if payload.storage_limit_mb is not None:
        target_user.storage_limit = payload.storage_limit_mb * 1024 * 1024
    else:
        target_user.storage_limit = None

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