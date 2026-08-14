from datetime import datetime, timezone
from sqlalchemy import Column, String, ForeignKey, TIMESTAMP, Boolean, text, Enum as SQLEnum
from sqlalchemy.orm import relationship, backref
from app.core.database.database import Base
from app.enum.enum import HubPrivacy

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(String, primary_key=True, index=True)
    type = Column(String, default="DM") # DM, GROUP, DEPARTMENT, CLUB, STUDY_GROUP
    name = Column(String, nullable=True)
    
    description = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    privacy = Column(SQLEnum(HubPrivacy), default=HubPrivacy.PUBLIC, nullable=False)
    institution_id = Column(String, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=True)
    
    department_id = Column(String, ForeignKey("departments.id", ondelete="CASCADE"), nullable=True)
    parent_id = Column(String, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), nullable=False)
    
    participants = relationship("ConversationParticipant", back_populates="conversation", cascade="all, delete-orphan")
    sub_hubs = relationship("Conversation", backref=backref("parent", remote_side=[id]), cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="asc(Message.created_at)")

class ConversationParticipant(Base):
    __tablename__ = "conversation_participants"
    
    id = Column(String, primary_key=True, index=True)
    conversation_id = Column(String, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    is_blocked = Column(Boolean, default=False)
    
    is_admin = Column(Boolean, default=False)
    is_lead = Column(Boolean, default=False)
    is_approved = Column(Boolean, default=True)
    
    conversation = relationship("Conversation", back_populates="participants")
    user = relationship("User")

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(String, primary_key=True, index=True)
    conversation_id = Column(String, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    sender_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), nullable=False)
    
    reply_to_id = Column(String, ForeignKey("messages.id", ondelete="SET NULL"), nullable=True)
    is_delivered = Column(Boolean, default=False)
    is_read = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    is_edited = Column(Boolean, default=False)
    
    conversation = relationship("Conversation", back_populates="messages")
    sender = relationship("User")
    reply_to = relationship("Message", remote_side=[id], uselist=False)

class SavedHub(Base):
    __tablename__ = "saved_hubs"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    hub_id = Column(String, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), nullable=False)