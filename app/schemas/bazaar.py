from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime
from app.enum.enum import BazaarCategory, ItemCondition

class ProductSeller(BaseModel):
    id: str
    first_name: str
    last_name: str
    
    class Config:
        from_attributes = True

class ProductCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=100)
    description: str = Field(..., min_length=10, max_length=1000)
    price: float = Field(..., ge=0)
    category: BazaarCategory
    condition: ItemCondition
    image_url: Optional[str] = None

class ProductUpdate(BaseModel):
    is_sold: Optional[bool] = None

class ProductResponse(BaseModel):
    id: str
    title: str
    description: str
    price: float
    category: BazaarCategory
    condition: ItemCondition
    image_url: Optional[str]
    is_sold: bool
    created_at: datetime
    seller: ProductSeller
    is_saved: Optional[bool] = False
    
    class Config:
        from_attributes = True