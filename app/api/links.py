import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database.database import get_db
from app.models import models
from app.schemas.square import UsefulLinkCreate, UsefulLinkResponse
from app.core.auth.oauth2 import get_current_user
from app.enum.enum import UserRole

router = APIRouter(
    prefix="/api/links",
    tags=["Useful Links"]
)

@router.get("", response_model=List[UsefulLinkResponse])
def get_useful_links(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(models.UsefulLink).filter(
        models.UsefulLink.institution_id == current_user.institution_id,
        models.UsefulLink.is_active == True
    ).order_by(models.UsefulLink.created_at.desc()).all()


@router.post("", response_model=UsefulLinkResponse, status_code=status.HTTP_201_CREATED)
def create_useful_link(
    payload: UsefulLinkCreate, 
    current_user: models.User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    if current_user.role not in [UserRole.ADMIN, UserRole.COMMUNITY_HEAD]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Only administrators and community heads can manage useful links."
        )
        
    new_link = models.UsefulLink(
        id=str(uuid.uuid4()),
        title=payload.title.strip(),
        url=payload.url.strip(),
        icon_name=payload.icon_name,
        is_active=payload.is_active,
        institution_id=current_user.institution_id
    )
    
    db.add(new_link)
    db.commit()
    db.refresh(new_link)
    return new_link


@router.delete("/{link_id}", status_code=status.HTTP_200_OK)
def delete_useful_link(link_id: str, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role not in [UserRole.ADMIN, UserRole.COMMUNITY_HEAD]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized.")
        
    link = db.query(models.UsefulLink).filter(
        models.UsefulLink.id == link_id, 
        models.UsefulLink.institution_id == current_user.institution_id
    ).first()
    
    if not link:
        raise HTTPException(status_code=404, detail="Link not found.")
        
    db.delete(link)
    db.commit()
    return {"success": True, "message": "Link successfully removed."}