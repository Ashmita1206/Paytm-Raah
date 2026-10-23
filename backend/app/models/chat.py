import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database.session import Base
from app.utils.time_utils import utcnow

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String(64), primary_key=True, default=lambda: f"sess_{uuid.uuid4().hex[:12]}")
    user_id = Column(String(64), ForeignKey("users.id"), nullable=False, index=True)
    transaction_id = Column(String(64), nullable=True, index=True)
    case_id = Column(String(64), nullable=True, index=True)
    
    title = Column(String(150), default="Payment Inquiry")
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", order_by="ChatMessage.created_at.asc()", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String(64), primary_key=True, default=lambda: f"msg_{uuid.uuid4().hex[:12]}")
    session_id = Column(String(64), ForeignKey("chat_sessions.id"), nullable=False, index=True)
    
    # Sender: USER, ASSISTANT, SYSTEM, TOOL
    sender = Column(String(30), nullable=False)
    content = Column(Text, nullable=False)
    
    # Agent activity details
    tool_calls = Column(Text, default="[]")      # JSON array of tools executed
    tool_results = Column(Text, default="[]")    # JSON array of tool outputs
    metadata_json = Column(Text, default="{}")   # JSON payload
    
    created_at = Column(DateTime(timezone=True), default=utcnow)

    session = relationship("ChatSession", back_populates="messages")
