import uuid
import json
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database.session import Base
from app.utils.time_utils import utcnow

class ResolutionCase(Base):
    __tablename__ = "resolution_cases"

    id = Column(String(64), primary_key=True, default=lambda: f"case_{uuid.uuid4().hex[:12]}")
    case_number = Column(String(32), unique=True, index=True, nullable=False)
    transaction_id = Column(String(64), ForeignKey("transactions.id"), unique=True, nullable=False)
    user_id = Column(String(64), ForeignKey("users.id"), nullable=False, index=True)

    # Status: INVESTIGATING, RECOVERY_IN_PROGRESS, ESCALATED, RESOLVED, CLOSED
    status = Column(String(40), default="INVESTIGATING", index=True)
    category = Column(String(80), default="UPI_P2M_DEBIT_WITHOUT_CONFIRMATION")
    
    # Regulatory Policy Information
    policy_name = Column(String(100), default="RBI Harmonisation Circular - UPI P2M (T+5)")
    regulatory_deadline = Column(DateTime(timezone=True), nullable=True)
    policy_explanation = Column(Text, nullable=True)
    compensation_eligible = Column(Boolean, default=False)
    compensation_rate_inr = Column(Float, default=100.0)  # INR 100/day after turnaround time
    
    # Autonomous loop state
    assigned_agent = Column(String(50), default="RAAH_RESCUE")
    latest_ai_action = Column(String(255), default="Investigation initiated by Raah Rescue")
    last_checked_at = Column(DateTime(timezone=True), default=utcnow)
    next_check_at = Column(DateTime(timezone=True), nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=5)
    
    # Incident link if correlated
    correlated_incident_id = Column(String(64), nullable=True, index=True)
    
    resolution_summary = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    transaction = relationship("Transaction", back_populates="resolution_case")
    user = relationship("User", back_populates="cases")
    action_logs = relationship("CaseActionLog", back_populates="case", order_by="CaseActionLog.created_at.asc()", cascade="all, delete-orphan")
    followups = relationship("ScheduledFollowup", back_populates="case", cascade="all, delete-orphan")
    approval_requests = relationship("HumanApprovalRequest", back_populates="case", cascade="all, delete-orphan")


class CaseActionLog(Base):
    __tablename__ = "case_action_logs"

    id = Column(String(64), primary_key=True, default=lambda: f"act_{uuid.uuid4().hex[:12]}")
    case_id = Column(String(64), ForeignKey("resolution_cases.id"), nullable=False, index=True)
    agent_type = Column(String(40), default="RAAH_RESCUE")  # RAAH_RESCUE, RAAH_PULSE, HUMAN_OPS
    
    tool_invoked = Column(String(80), nullable=False)
    action_title = Column(String(150), nullable=False)
    action_description = Column(Text, nullable=True)
    
    input_payload = Column(Text, default="{}")
    output_payload = Column(Text, default="{}")
    
    # Outcomes: VALIDATED, REJECTED, BYPASSED
    validation_outcome = Column(String(30), default="VALIDATED")
    # Outcomes: SUCCESS, FAILURE, PARTIAL
    execution_outcome = Column(String(30), default="SUCCESS")
    
    audit_metadata = Column(Text, default="{}")
    created_at = Column(DateTime(timezone=True), default=utcnow)

    case = relationship("ResolutionCase", back_populates="action_logs")


class ScheduledFollowup(Base):
    __tablename__ = "scheduled_followups"

    id = Column(String(64), primary_key=True, default=lambda: f"fol_{uuid.uuid4().hex[:12]}")
    case_id = Column(String(64), ForeignKey("resolution_cases.id"), nullable=False, index=True)
    scheduled_for = Column(DateTime(timezone=True), nullable=False, index=True)
    status = Column(String(30), default="PENDING", index=True)  # PENDING, EXECUTED, CANCELLED
    action_type = Column(String(50), default="RECHECK_STATUS")
    retry_backoff_seconds = Column(Integer, default=60)
    payload = Column(Text, default="{}")
    created_at = Column(DateTime(timezone=True), default=utcnow)
    executed_at = Column(DateTime(timezone=True), nullable=True)

    case = relationship("ResolutionCase", back_populates="followups")


class HumanApprovalRequest(Base):
    __tablename__ = "human_approval_requests"

    id = Column(String(64), primary_key=True, default=lambda: f"apr_{uuid.uuid4().hex[:12]}")
    case_id = Column(String(64), ForeignKey("resolution_cases.id"), nullable=False, index=True)
    action_name = Column(String(80), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(30), default="PENDING")  # PENDING, APPROVED, REJECTED
    requested_by = Column(String(50), default="RAAH_RESCUE")
    approved_by = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    decided_at = Column(DateTime(timezone=True), nullable=True)

    case = relationship("ResolutionCase", back_populates="approval_requests")
