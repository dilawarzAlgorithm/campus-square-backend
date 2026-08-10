import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database.database import get_db
from app.models import models
from app.schemas import schemas
from app.core.auth.oauth2 import get_current_user
from app.enum.enum import BazaarCategory, UserRole
from app.core.features.storage import handle_file_deletion
from app.api.notification import trigger_push_notification

router = APIRouter(
    prefix="/api/bazaar",
    tags=["Bazaar (Marketplace)"]
)

@router.post("/products", response_model=schemas.ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: schemas.ProductCreate,
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    new_product = models.BazaarProduct(
        id=str(uuid.uuid4()),
        title=payload.title.strip(),
        description=payload.description.strip(),
        price=payload.price,
        category=payload.category,
        condition=payload.condition,
        image_url=payload.image_url,
        institution_id=current_user.institution_id,
        seller_id=current_user.id
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    background_tasks.add_task(
        trigger_push_notification,
        title="New in Bazaar",
        body=f"{current_user.first_name} listed '{new_product.title}' for ₹{new_product.price:.0f}.",
        topic=f"{current_user.institution_id}_all_notices",
        data_payload={"product_id": new_product.id, "type": "bazaar", "sender_id": current_user.id}
    )

    return new_product

@router.get("/products", response_model=List[schemas.ProductResponse])
def get_products(
    category: Optional[BazaarCategory] = None,
    include_sold: bool = False,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(models.BazaarProduct).filter(
        models.BazaarProduct.institution_id == current_user.institution_id
    )
    
    if category:
        query = query.filter(models.BazaarProduct.category == category)
    if not include_sold:
        query = query.filter(models.BazaarProduct.is_sold == False)
        
    products = query.order_by(models.BazaarProduct.created_at.desc()).all()
    
    product_ids = [p.id for p in products]
    saved_items = db.query(models.SavedProduct).filter(
        models.SavedProduct.user_id == current_user.id,
        models.SavedProduct.product_id.in_(product_ids)
    ).all()
    
    saved_map = {s.product_id: True for s in saved_items}
    for p in products:
        setattr(p, 'is_saved', saved_map.get(p.id, False))
        
    return products

@router.get("/my-products", response_model=List[schemas.ProductResponse])
def get_my_products(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    products = db.query(models.BazaarProduct).filter(
        models.BazaarProduct.seller_id == current_user.id
    ).order_by(models.BazaarProduct.created_at.desc()).all()
    return products

@router.patch("/products/{product_id}", response_model=schemas.ProductResponse)
def update_product(
    product_id: str,
    payload: schemas.ProductUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    product = db.query(models.BazaarProduct).filter(models.BazaarProduct.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
        
    if product.seller_id != current_user.id and current_user.role not in [UserRole.ADMIN, UserRole.COMMUNITY_HEAD]:
        raise HTTPException(status_code=403, detail="Not authorized.")
        
    if payload.is_sold is not None:
        product.is_sold = payload.is_sold
        
    db.commit()
    db.refresh(product)
    return product

@router.delete("/products/{product_id}")
def delete_product(
    product_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    product = db.query(models.BazaarProduct).filter(models.BazaarProduct.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
        
    if product.seller_id != current_user.id and current_user.role not in [UserRole.ADMIN, UserRole.COMMUNITY_HEAD]:
        raise HTTPException(status_code=403, detail="Not authorized.")
        
    img_url = product.image_url
    db.delete(product)
    db.commit()
    
    if img_url:
        handle_file_deletion(img_url, db)
        
    return {"success": True}

@router.post("/products/{product_id}/save")
def toggle_save_product(
    product_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    existing = db.query(models.SavedProduct).filter(
        models.SavedProduct.user_id == current_user.id,
        models.SavedProduct.product_id == product_id
    ).first()
    
    if existing:
        db.delete(existing)
        db.commit()
        return {"is_saved": False}
    else:
        new_save = models.SavedProduct(id=str(uuid.uuid4()), user_id=current_user.id, product_id=product_id)
        db.add(new_save)
        db.commit()
        return {"is_saved": True}