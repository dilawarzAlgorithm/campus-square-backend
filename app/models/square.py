from datetime import datetime, timezone
from sqlalchemy import Column, String, ForeignKey, Enum as SQLEnum, TIMESTAMP, text as sa_text, Integer
from sqlalchemy.orm import relationship, backref

from app.core.database.database import Base
from app.enum.enum import SquareCategory, VoteType

class Notice(Base):
    __tablename__ = "notices"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    body = Column(String, nullable=False)
    category = Column(SQLEnum(SquareCategory), default=SquareCategory.NOTICE, nullable=False)
    
    urgent_until = Column(TIMESTAMP(timezone=True), nullable=True) 
    image_url = Column(String, nullable=True)
    file_url = Column(String, nullable=True)
    
    upvote_count = Column(Integer, default=0, server_default="0", nullable=False)
    downvote_count = Column(Integer, default=0, server_default="0", nullable=False)
    
    created_at = Column(TIMESTAMP(timezone=True), server_default=sa_text('now()'), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=sa_text('now()'), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    institution_id = Column(String, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False)
    author_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    institution = relationship("Institution")
    author = relationship("User")
    
    comments = relationship("NoticeComment", back_populates="notice", cascade="all, delete-orphan", order_by="desc(NoticeComment.created_at)")
    votes = relationship("NoticeVote", back_populates="notice", cascade="all, delete-orphan")

class NoticeVote(Base):
    __tablename__ = "notice_votes"
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    notice_id = Column(String, ForeignKey("notices.id", ondelete="CASCADE"), nullable=False)
    vote_type = Column(SQLEnum(VoteType), nullable=False)
    
    user = relationship("User")
    notice = relationship("Notice", back_populates="votes")

class NoticeComment(Base):
    __tablename__ = "notice_comments"

    id = Column(String, primary_key=True, index=True)
    text = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=sa_text('now()'), nullable=False)

    parent_id = Column(String, ForeignKey("notice_comments.id", ondelete="CASCADE"), nullable=True)
    
    notice_id = Column(String, ForeignKey("notices.id", ondelete="CASCADE"), nullable=False)
    author_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    notice = relationship("Notice", back_populates="comments")
    author = relationship("User")

    replies = relationship("NoticeComment", backref=backref('parent', remote_side=[id]), cascade="all, delete-orphan")