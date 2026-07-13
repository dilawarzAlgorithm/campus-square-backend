import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session

from app.core.database.database import get_db
from app.models import models
from app.schemas import schemas
from app.core.auth.oauth2 import get_current_user
from app.enum.enum import ResourceType, VoteType, UserRole
from app.core.features.storage import upload_file_to_supabase

router = APIRouter(
    prefix="/api/vault",
    tags=["Academic Vault"]
)

@router.post("/departments", response_model=schemas.DepartmentResponse, status_code=status.HTTP_201_CREATED)
def create_department(
    payload: schemas.DepartmentCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    dept_code = payload.code.strip().upper()

    existing_dept = db.query(models.Department).filter(
        models.Department.code == dept_code,
        models.Department.institution_id == current_user.institution_id
    ).first()

    if existing_dept:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A department with code '{dept_code}' is already registered at your institution."
        )

    new_dept = models.Department(
        id=str(uuid.uuid4()),
        name=payload.name.strip(),
        code=dept_code,
        institution_id=current_user.institution_id
    )
    db.add(new_dept)
    db.commit()
    db.refresh(new_dept)
    return new_dept


@router.get("/departments", response_model=List[schemas.DepartmentResponse])
def get_departments(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(models.Department).filter(
        models.Department.institution_id == current_user.institution_id
    ).order_by(models.Department.code.asc()).all()


@router.post("/upload-file", status_code=status.HTTP_200_OK)
async def upload_resource_file(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user)
):
    file_bytes = await file.read()
    
    file_url = upload_file_to_supabase(
        file_bytes=file_bytes,
        original_filename=file.filename,
        content_type=file.content_type
    )
    
    return {"success": True, "file_url": file_url}


@router.post("/resources", response_model=schemas.ResourceResponse, status_code=status.HTTP_201_CREATED)
def upload_resource(
    payload: schemas.ResourceCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    department = db.query(models.Department).filter(
        models.Department.id == payload.department_id,
        models.Department.institution_id == current_user.institution_id
    ).first()

    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The target department was not found or belongs to another institution."
        )

    new_resource = models.AcademicResource(
        id=str(uuid.uuid4()),
        title=payload.title.strip(),
        description=payload.description.strip() if payload.description else None,
        file_url=payload.file_url.strip(),
        resource_type=payload.resource_type,
        semester=payload.semester,
        department_id=payload.department_id,
        uploader_id=current_user.id
    )
    db.add(new_resource)
    
    current_user.karma += 10
    
    db.commit()
    db.refresh(new_resource)
    return new_resource


@router.get("/resources", response_model=List[schemas.ResourceResponse])
def get_resources(
    department_id: Optional[str] = None,
    semester: Optional[int] = Query(None, ge=1, le=8),
    resource_type: Optional[ResourceType] = None,
    sort_by: str = Query("upvotes", pattern="^(upvotes|newest)$"),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(models.AcademicResource).join(models.Department).filter(
        models.Department.institution_id == current_user.institution_id
    )

    if department_id:
        query = query.filter(models.AcademicResource.department_id == department_id)
    if semester:
        query = query.filter(models.AcademicResource.semester == semester)
    if resource_type:
        query = query.filter(models.AcademicResource.resource_type == resource_type)

    if sort_by == "newest":
        query = query.order_by(models.AcademicResource.created_at.desc())
    else:
        query = query.order_by(models.AcademicResource.upvote_count.desc(), models.AcademicResource.created_at.desc())

    return query.all()

@router.delete("/resources/{resource_id}", status_code=status.HTTP_200_OK)
def delete_resource(
    resource_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    resource = db.query(models.AcademicResource).join(models.Department).filter(
        models.AcademicResource.id == resource_id,
        models.Department.institution_id == current_user.institution_id
    ).first()

    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The requested academic resource does not exist or belongs to another institution."
        )

    if resource.uploader_id != current_user.id and current_user.role not in [UserRole.ADMIN, UserRole.COMMUNITY_HEAD]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this resource."
        )

    db.delete(resource)
    db.commit()

    return {"success": True, "message": "Resource successfully deleted."}

@router.post("/resources/{resource_id}/vote", response_model=schemas.ResourceResponse)
def vote_resource(
    resource_id: str,
    payload: schemas.VoteRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    resource = db.query(models.AcademicResource).join(models.Department).filter(
        models.AcademicResource.id == resource_id,
        models.Department.institution_id == current_user.institution_id
    ).first()

    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The requested academic resource does not exist or belongs to another institution."
        )

    uploader = db.query(models.User).filter(models.User.id == resource.uploader_id).first()

    existing_vote = db.query(models.ResourceVote).filter(
        models.ResourceVote.user_id == current_user.id,
        models.ResourceVote.resource_id == resource_id
    ).first()

    if existing_vote:
        if existing_vote.vote_type == payload.vote_type:
            # Do nothing if again clicked on same vote type.
            # pass
            # To toggle, un-comment this ->
            if payload.vote_type == VoteType.UPVOTE:
                resource.upvote_count = max(0, resource.upvote_count - 1)
                if uploader:
                    uploader.karma = max(0, uploader.karma - 5)
            else:
                resource.downvote_count = max(0, resource.downvote_count - 1)
            
            db.delete(existing_vote)

        else:
            if payload.vote_type == VoteType.UPVOTE:
                resource.upvote_count += 1
                resource.downvote_count = max(0, resource.downvote_count - 1)
                if uploader:
                    uploader.karma += 5
            else:
                resource.downvote_count += 1
                resource.upvote_count = max(0, resource.upvote_count - 1)
                if uploader:
                    uploader.karma = max(0, uploader.karma - 5)

            existing_vote.vote_type = payload.vote_type

    else:
        new_vote = models.ResourceVote(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            resource_id=resource_id,
            vote_type=payload.vote_type
        )
        db.add(new_vote)

        if payload.vote_type == VoteType.UPVOTE:
            resource.upvote_count += 1
            if uploader:
                uploader.karma += 5
        else:
            resource.downvote_count += 1

    db.commit()
    db.refresh(resource)
    return resource