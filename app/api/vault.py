import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database.database import get_db
from app.models import models
from app.schemas import schemas
from app.core.auth.oauth2 import get_current_user

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
