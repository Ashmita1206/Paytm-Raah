import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database.session import Base
from app.utils.time_utils import utcnow

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(64), primary_key=True, default=lambda: f"notif_{uuid.uuid4().hex[:12]}")
    user_id = Column(String(64), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(150), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(50), default="CASE_UPDATE")  # CASE_UPDATE, RETRYGUARD_ALERT, INCIDENT_NOTICE
    read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    user = relationship("User", back_populates="notifications")
