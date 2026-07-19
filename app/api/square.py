import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database.database import get_db
from app.models import models
from app.schemas import schemas
from app.core.auth.oauth2 import get_current_user
from app.enum.enum import SquareCategory, UserRole

router = APIRouter(
    prefix="/api/square",
    tags=["Square (Notices)"]
)

@router.post("/notices", response_model=schemas.NoticeResponse, status_code=status.HTTP_201_CREATED)
def create_notice(
    payload: schemas.NoticeCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    official_categories = [SquareCategory.NOTICE, SquareCategory.EVENT]
    
    if payload.category in official_categories:
        if current_user.role not in [UserRole.ADMIN, UserRole.COMMUNITY_HEAD]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail=f"Only administrators and community heads can post official {payload.category.value}s."
            )

    new_notice = models.Notice(
        id=str(uuid.uuid4()),
        title=payload.title.strip(),
        body=payload.body.strip(),
        category=payload.category,
        urgent_until=payload.urgent_until,
        image_url=payload.image_url,
        file_url=payload.file_url,
        institution_id=current_user.institution_id,
        author_id=current_user.id
    )

    db.add(new_notice)
    db.commit()
    db.refresh(new_notice)
    return new_notice

@router.get("/notices", response_model=List[schemas.NoticeResponse])
def get_notices(
    category: Optional[SquareCategory] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(models.Notice).filter(
        models.Notice.institution_id == current_user.institution_id
    )

    if category:
        query = query.filter(models.Notice.category == category)

    return query.order_by(models.Notice.created_at.desc()).all()

@router.delete("/notices/{notice_id}", status_code=status.HTTP_200_OK)
def delete_notice(
    notice_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notice = db.query(models.Notice).filter(
        models.Notice.id == notice_id,
        models.Notice.institution_id == current_user.institution_id
    ).first()

    if not notice:
        raise HTTPException(status_code=404, detail="Notice not found.")

    is_owner = notice.author_id == current_user.id
    is_staff = current_user.role in [UserRole.ADMIN, UserRole.COMMUNITY_HEAD]

    if not (is_owner or is_staff):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Not authorized to delete this post."
        )

    db.delete(notice)
    db.commit()
    return {"success": True, "message": "Post deleted successfully."}

@router.post("/notices/{notice_id}/comments", response_model=schemas.CommentResponse, status_code=status.HTTP_201_CREATED)
def add_comment(
    notice_id: str,
    payload: schemas.CommentCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notice = db.query(models.Notice).filter(
        models.Notice.id == notice_id,
        models.Notice.institution_id == current_user.institution_id
    ).first()

    if not notice:
        raise HTTPException(status_code=404, detail="Notice not found.")
    
    if payload.parent_id:
        parent_comment = db.query(models.NoticeComment).filter(models.NoticeComment.id == payload.parent_id).first()
        if not parent_comment:
             raise HTTPException(status_code=404, detail="Parent comment not found.")

    new_comment = models.NoticeComment(
        id=str(uuid.uuid4()),
        text=payload.text.strip(),
        notice_id=notice.id,
        author_id=current_user.id,
        parent_id=payload.parent_id
    )
    
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    return new_comment

@router.delete("/comments/{comment_id}", status_code=status.HTTP_200_OK)
def delete_comment(
    comment_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    comment = db.query(models.NoticeComment).filter(models.NoticeComment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found.")

    is_owner = comment.author_id == current_user.id
    is_staff = current_user.role in [UserRole.ADMIN, UserRole.COMMUNITY_HEAD]

    if not (is_owner or is_staff):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this comment.")

    db.delete(comment)
    db.commit()
    return {"success": True, "message": "Comment deleted."}