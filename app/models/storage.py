from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP, text
from app.core.database.database import Base

class FileAsset(Base):
    __tablename__ = "file_assets"
    id = Column(String, primary_key=True, index=True)
    file_hash = Column(String, unique=True, index=True, nullable=False)
    file_url = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    uploader_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), nullable=False)
