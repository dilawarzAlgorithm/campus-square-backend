import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database.database import get_db
from app.models import models
from app.schemas import schemas
from app.core.auth.oauth2 import get_current_user
from app.enum.enum import SquareCategory, UserRole, VoteType
from app.core.features.storage import handle_file_deletion
from app.api.notification import trigger_push_notification

router = APIRouter(
    prefix="/api/square",
    tags=["Square (Notices)"]
)

@router.post("/notices", response_model=schemas.NoticeResponse, status_code=status.HTTP_201_CREATED)
def create_notice(
    payload: schemas.NoticeCreate,
    background_tasks: BackgroundTasks,
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

    if payload.category in official_categories or payload.urgent_until:
        topic = f"{current_user.institution_id}_important_notices" if payload.urgent_until else f"{current_user.institution_id}_all_notices"
        title_prefix = "Urgent Notice" if payload.urgent_until else payload.category.value.title()
        body_snippet = payload.body[:100] + ("..." if len(payload.body) > 100 else "")
        
        background_tasks.add_task(
            trigger_push_notification,
            title=f"{title_prefix}: {payload.title}",
            body=body_snippet,
            topic=topic,
            data_payload={"notice_id": new_notice.id, "type": "square", "sender_id": current_user.id}
        )

    return new_notice

@router.get("/notices", response_model=List[schemas.NoticeResponse])
def get_notices(
    category: Optional[SquareCategory] = None,
    sort_by: str = Query("newest"),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(models.Notice).filter(
        models.Notice.institution_id == current_user.institution_id
    )

    if category:
        query = query.filter(models.Notice.category == category)
        if sort_by == "upvotes":
            query = query.order_by(desc(models.Notice.upvote_count), desc(models.Notice.created_at))
        else:
            query = query.order_by(desc(models.Notice.created_at))
    else:
        query = query.filter(models.Notice.category != SquareCategory.RANDOM)
        query = query.order_by(desc(models.Notice.created_at))

    notices = query.all()

    notice_ids = [n.id for n in notices]
    user_votes = db.query(models.NoticeVote).filter(
        models.NoticeVote.user_id == current_user.id,
        models.NoticeVote.notice_id.in_(notice_ids)
    ).all()
    
    vote_map = {v.notice_id: v.vote_type for v in user_votes}

    for n in notices:
        setattr(n, 'my_vote', vote_map.get(n.id))
        
    return notices

@router.post("/notices/{notice_id}/vote", response_model=schemas.NoticeResponse)
def vote_notice(
    notice_id: str,
    payload: schemas.VoteRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notice = db.query(models.Notice).filter(
        models.Notice.id == notice_id,
        models.Notice.institution_id == current_user.institution_id
    ).first()

    if not notice:
        raise HTTPException(status_code=404, detail="Notice not found.")

    author = db.query(models.User).filter(models.User.id == notice.author_id).first()

    existing_vote = db.query(models.NoticeVote).filter(
        models.NoticeVote.user_id == current_user.id,
        models.NoticeVote.notice_id == notice_id
    ).first()

    if existing_vote:
        if existing_vote.vote_type == payload.vote_type:
            if payload.vote_type == VoteType.UPVOTE:
                notice.upvote_count = max(0, notice.upvote_count - 1)
                if author: author.karma = max(0, author.karma - 2)
            else:
                notice.downvote_count = max(0, notice.downvote_count - 1)
            db.delete(existing_vote)
        else:
            if payload.vote_type == VoteType.UPVOTE:
                notice.upvote_count += 1
                notice.downvote_count = max(0, notice.downvote_count - 1)
                if author: author.karma += 2
            else:
                notice.downvote_count += 1
                notice.upvote_count = max(0, notice.upvote_count - 1)
                if author: author.karma = max(0, author.karma - 2)
            existing_vote.vote_type = payload.vote_type
    else:
        new_vote = models.NoticeVote(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            notice_id=notice_id,
            vote_type=payload.vote_type
        )
        db.add(new_vote)
        if payload.vote_type == VoteType.UPVOTE:
            notice.upvote_count += 1
            if author: author.karma += 2
        else:
            notice.downvote_count += 1

    db.commit()
    db.refresh(notice)

    final_vote = db.query(models.NoticeVote).filter(
        models.NoticeVote.user_id == current_user.id,
        models.NoticeVote.notice_id == notice_id
    ).first()
    
    setattr(notice, 'my_vote', final_vote.vote_type if final_vote else None)

    return notice

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
        
    image_url = notice.image_url
    file_url = notice.file_url

    db.delete(notice)
    db.commit()

    if image_url: handle_file_deletion(image_url, db)
    if file_url: handle_file_deletion(file_url, db)
    
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