import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database.database import get_db
from app.models import models
from app.schemas import hub as hub_schemas
from app.core.auth.oauth2 import get_current_user
from app.enum.enum import UserRole, HubPrivacy
from app.api.notification import send_token_push_notification

router = APIRouter(prefix="/api/hubs", tags=["Campus Hubs (Clubs & Study Groups)"])

@router.get("", response_model=List[hub_schemas.HubResponse])
def get_hubs(type: Optional[str] = None, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(models.Conversation).filter(
        models.Conversation.institution_id == current_user.institution_id,
        models.Conversation.type.in_(["CLUB", "STUDY_GROUP"])
    )
    if type:
        query = query.filter(models.Conversation.type == type)

    conversations = query.all()
    result = []
    
    saved_hubs = db.query(models.SavedHub).filter_by(user_id=current_user.id).all()
    saved_map = {s.hub_id: True for s in saved_hubs}
    
    for conv in conversations:
        member_count = db.query(models.ConversationParticipant).filter_by(conversation_id=conv.id, is_approved=True).count()
        participant = db.query(models.ConversationParticipant).filter_by(conversation_id=conv.id, user_id=current_user.id).first()

        is_member = participant is not None and participant.is_approved
        is_pending = participant is not None and not participant.is_approved
        is_admin = participant is not None and participant.is_admin
        is_saved = saved_map.get(conv.id, False)

        result.append(hub_schemas.HubResponse(
            id=conv.id,
            name=conv.name,
            description=conv.description,
            type=conv.type,
            privacy=conv.privacy,
            avatar_url=conv.avatar_url,
            member_count=member_count,
            is_member=is_member,
            is_admin=is_admin,
            is_pending=is_pending,
            is_saved=is_saved,
            created_at=conv.created_at
        ))
    return result

@router.post("", response_model=hub_schemas.HubResponse)
def create_hub(payload: hub_schemas.HubCreate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if payload.type == "CLUB" and current_user.role not in [UserRole.ADMIN, UserRole.COMMUNITY_HEAD]:
        raise HTTPException(status_code=403, detail="Only staff can create official clubs.")

    new_hub = models.Conversation(
        id=str(uuid.uuid4()),
        type=payload.type,
        name=payload.name.strip(),
        description=payload.description.strip(),
        privacy=payload.privacy,
        avatar_url=payload.avatar_url,
        institution_id=current_user.institution_id
    )
    db.add(new_hub)
    db.flush()

    admin_participant = models.ConversationParticipant(
        id=str(uuid.uuid4()),
        conversation_id=new_hub.id,
        user_id=current_user.id,
        is_admin=True,
        is_approved=True
    )
    db.add(admin_participant)
    db.commit()

    return hub_schemas.HubResponse(
        id=new_hub.id,
        name=new_hub.name,
        description=new_hub.description,
        type=new_hub.type,
        privacy=new_hub.privacy,
        avatar_url=new_hub.avatar_url,
        member_count=1,
        is_member=True,
        is_admin=True,
        is_pending=False,
        is_saved=False,
        created_at=new_hub.created_at
    )

@router.post("/{hub_id}/join")
def join_hub(hub_id: str, background_tasks: BackgroundTasks, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    hub = db.query(models.Conversation).filter_by(id=hub_id, institution_id=current_user.institution_id).first()
    if not hub: 
        raise HTTPException(status_code=404, detail="Hub not found")

    existing = db.query(models.ConversationParticipant).filter_by(conversation_id=hub_id, user_id=current_user.id).first()
    if existing:
        return {"message": "Already requested or joined.", "is_pending": not existing.is_approved}

    is_approved = hub.privacy == HubPrivacy.PUBLIC

    p = models.ConversationParticipant(
        id=str(uuid.uuid4()),
        conversation_id=hub_id,
        user_id=current_user.id,
        is_approved=is_approved
    )
    db.add(p)
    db.commit()
    
    if not is_approved:
        admins = db.query(models.ConversationParticipant).filter(
            models.ConversationParticipant.conversation_id == hub.id,
            models.ConversationParticipant.is_admin == True
        ).all()
        for admin in admins:
            admin_user = db.query(models.User).filter(models.User.id == admin.user_id).first()
            if admin_user and admin_user.fcm_token:
                background_tasks.add_task(
                    send_token_push_notification,
                    title="New Join Request",
                    body=f"{current_user.first_name} requested to join {hub.name}",
                    token=admin_user.fcm_token,
                    data_payload={"conversation_id": hub.id, "type": "chat"}
                )

    return {"message": "Joined successfully" if is_approved else "Join request sent to Admins", "is_pending": not is_approved}

@router.post("/{hub_id}/leave")
def leave_hub(hub_id: str, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    p = db.query(models.ConversationParticipant).filter_by(conversation_id=hub_id, user_id=current_user.id).first()
    if p:
        db.delete(p)
        db.commit()
    return {"success": True}

@router.post("/{hub_id}/save")
def toggle_save_hub(hub_id: str, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    existing = db.query(models.SavedHub).filter_by(hub_id=hub_id, user_id=current_user.id).first()
    if existing:
        db.delete(existing)
        db.commit()
        return {"is_saved": False}
    else:
        new_save = models.SavedHub(id=str(uuid.uuid4()), user_id=current_user.id, hub_id=hub_id)
        db.add(new_save)
        db.commit()
        return {"is_saved": True}

@router.patch("/{hub_id}/members/{user_id}/approve")
def approve_member(hub_id: str, user_id: str, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    admin_check = db.query(models.ConversationParticipant).filter_by(conversation_id=hub_id, user_id=current_user.id, is_admin=True).first()
    if not admin_check and current_user.role not in [UserRole.ADMIN, UserRole.COMMUNITY_HEAD]:
        raise HTTPException(status_code=403, detail="Not authorized to approve members.")
        
    participant = db.query(models.ConversationParticipant).filter_by(conversation_id=hub_id, user_id=user_id).first()
    if not participant: raise HTTPException(status_code=404, detail="User request not found")
    
    participant.is_approved = True
    db.commit()
    return {"success": True, "message": "Member approved"}

@router.delete("/{hub_id}/members/{user_id}/reject")
def reject_member(hub_id: str, user_id: str, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    admin_check = db.query(models.ConversationParticipant).filter_by(conversation_id=hub_id, user_id=current_user.id, is_admin=True).first()
    if not admin_check and current_user.role not in [UserRole.ADMIN, UserRole.COMMUNITY_HEAD]:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    participant = db.query(models.ConversationParticipant).filter_by(conversation_id=hub_id, user_id=user_id).first()
    if participant:
        db.delete(participant)
        db.commit()
    return {"success": True, "message": "Member rejected"}

@router.patch("/{hub_id}/members/{user_id}/promote")
def promote_member(hub_id: str, user_id: str, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    admin_check = db.query(models.ConversationParticipant).filter_by(conversation_id=hub_id, user_id=current_user.id, is_admin=True).first()
    if not admin_check and current_user.role not in [UserRole.ADMIN, UserRole.COMMUNITY_HEAD]:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    participant = db.query(models.ConversationParticipant).filter_by(conversation_id=hub_id, user_id=user_id).first()
    if not participant: raise HTTPException(status_code=404)
    
    participant.is_admin = True
    db.commit()
    return {"success": True, "message": "Member promoted to Admin"}

@router.patch("/{hub_id}/members/{user_id}/demote")
def demote_member(hub_id: str, user_id: str, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    admin_check = db.query(models.ConversationParticipant).filter_by(conversation_id=hub_id, user_id=current_user.id, is_admin=True).first()
    if not admin_check and current_user.role not in [UserRole.ADMIN, UserRole.COMMUNITY_HEAD]:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    participant = db.query(models.ConversationParticipant).filter_by(conversation_id=hub_id, user_id=user_id).first()
    if not participant: raise HTTPException(status_code=404)
    
    participant.is_admin = False
    db.commit()
    return {"success": True, "message": "Member demoted"}