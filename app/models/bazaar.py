from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Boolean, ForeignKey, Enum as SQLEnum, TIMESTAMP, text
from sqlalchemy.orm import relationship
from app.core.database.database import Base
from app.enum.enum import BazaarCategory, ItemCondition

class BazaarProduct(Base):
    __tablename__ = "bazaar_products"
    
    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    category = Column(SQLEnum(BazaarCategory), nullable=False)
    condition = Column(SQLEnum(ItemCondition), nullable=False)
    image_url = Column(String, nullable=True)
    is_sold = Column(Boolean, default=False, nullable=False)
    
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), nullable=False)
    
    institution_id = Column(String, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False)
    seller_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    seller = relationship("User")

class SavedProduct(Base):
    __tablename__ = "saved_products"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(String, ForeignKey("bazaar_products.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), nullable=False)
    
    user = relationship("User")
    product = relationship("BazaarProduct")