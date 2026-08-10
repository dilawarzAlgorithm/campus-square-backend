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
from app.schemas.config import AppConfigUpdate, AppConfigResponse

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

@router.patch("/campaign/global")
def update_global_campaign(
    payload: AppConfigUpdate, 
    current_user: models.User = Depends(require_admin), 
    db: Session = Depends(get_db)
):
    institutions = db.query(models.Institution).all()
    
    for inst in institutions:
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
    return {"success": True, "message": f"Successfully updated campaign for {len(institutions)} institutions."}

@router.get("/institutions/{institution_id}/campaign", response_model=AppConfigResponse)
def get_inst_campaign(institution_id: str, current_user: models.User = Depends(require_admin), db: Session = Depends(get_db)):
    inst = db.query(models.Institution).filter(models.Institution.id == institution_id).first()
    if not inst: raise HTTPException(status_code=404, detail="Institution not found")
        
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

@router.patch("/institutions/{institution_id}/campaign", response_model=AppConfigResponse)
def update_inst_campaign(institution_id: str, payload: AppConfigUpdate, current_user: models.User = Depends(require_admin), db: Session = Depends(get_db)):
    inst = db.query(models.Institution).filter(models.Institution.id == institution_id).first()
    if not inst: raise HTTPException(status_code=404, detail="Institution not found")
        
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
        domain=payload.domain,
        default_storage_limit=payload.default_storage_limit_mb * 1024 * 1024 if payload.default_storage_limit_mb else 52428800
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

@router.patch("/institutions/{institution_id}/storage-limit", response_model=schemas.InstitutionResponse)
def update_inst_storage_limit(
    institution_id: str,
    payload: schemas.InstitutionStorageLimitRequest,
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    inst = db.query(models.Institution).filter(models.Institution.id == institution_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found.")
    
    inst.default_storage_limit = payload.default_storage_limit_mb * 1024 * 1024
    db.commit()
    db.refresh(inst)
    return inst

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