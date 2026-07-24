from datetime import datetime, timezone
from sqlalchemy import Column, String, ForeignKey, TIMESTAMP, Boolean, text
from sqlalchemy.orm import relationship
from app.core.database.database import Base

class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(String, primary_key=True, index=True)
    type = Column(String, default="DM") # DM, GROUP, DEPARTMENT, etc.
    name = Column(String, nullable=True)
    department_id = Column(String, ForeignKey("departments.id", ondelete="CASCADE"), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), nullable=False)
    
    participants = relationship("ConversationParticipant", back_populates="conversation", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="asc(Message.created_at)")

class ConversationParticipant(Base):
    __tablename__ = "conversation_participants"
    id = Column(String, primary_key=True, index=True)
    conversation_id = Column(String, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    is_blocked = Column(Boolean, default=False)
    
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