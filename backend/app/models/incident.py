import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database.session import Base
from app.utils.time_utils import utcnow

class IncidentRecord(Base):
    __tablename__ = "incident_records"

    id = Column(String(64), primary_key=True, default=lambda: f"inc_{uuid.uuid4().hex[:12]}")
    incident_number = Column(String(32), unique=True, index=True, nullable=False)
    title = Column(String(150), nullable=False)
    error_category = Column(String(60), nullable=False, index=True)
    provider = Column(String(60), default="NPCI_UPI_SWITCH")
    bank = Column(String(60), default="HDFC Bank", index=True)
    
    affected_count = Column(Integer, default=1)
    baseline_failure_rate = Column(Float, default=1.2)  # Percentage
    observed_failure_rate = Column(Float, default=28.4)  # Percentage
    
    # Status: DETECTED, INVESTIGATING, CORRELATED, MITIGATED, RESOLVED
    status = Column(String(40), default="DETECTED", index=True)
    
    summary = Column(Text, nullable=True)
    recommended_mitigation = Column(Text, nullable=True)
    ai_actions_taken = Column(Text, default="[]")  # JSON array
    
    detected_at = Column(DateTime(timezone=True), default=utcnow)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    linked_cases = relationship("IncidentTransactionLink", back_populates="incident", cascade="all, delete-orphan")


class IncidentTransactionLink(Base):
    __tablename__ = "incident_transaction_links"

    id = Column(String(64), primary_key=True, default=lambda: f"link_{uuid.uuid4().hex[:12]}")
    incident_id = Column(String(64), ForeignKey("incident_records.id"), nullable=False, index=True)
    transaction_id = Column(String(64), nullable=False, index=True)
    case_id = Column(String(64), nullable=True, index=True)
    correlation_confidence = Column(Float, default=0.98)
    linked_at = Column(DateTime(timezone=True), default=utcnow)

    incident = relationship("IncidentRecord", back_populates="linked_cases")
