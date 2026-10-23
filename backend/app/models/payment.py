import uuid
import json
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.database.session import Base
from app.utils.time_utils import utcnow

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String(64), primary_key=True, default=lambda: f"tx_{uuid.uuid4().hex[:12]}")
    user_id = Column(String(64), ForeignKey("users.id"), nullable=False, index=True)
    merchant_id = Column(String(64), ForeignKey("demo_merchants.id"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="INR")
    
    # Status: PENDING, SUCCESS, FAILED, OUTCOME_UNKNOWN, DEBIT_REPORTED, REVERSED
    status = Column(String(30), default="PENDING", index=True)
    
    provider = Column(String(50), default="UPI_SIMULATOR")  # RAZORPAY_TEST, UPI_SIMULATOR
    upi_ref_no = Column(String(64), unique=True, nullable=True, index=True)
    idempotency_key = Column(String(64), unique=True, nullable=True, index=True)
    
    error_code = Column(String(50), nullable=True)
    failure_reason = Column(Text, nullable=True)
    
    # Bank & provider details for correlation
    payer_bank = Column(String(50), default="HDFC Bank")
    beneficiary_bank = Column(String(50), default="ICICI Bank")
    gateway = Column(String(50), default="NPCI_UPI_SWITCH")
    
    # Flags
    is_synthetic = Column(Boolean, default=True)
    client_response_dropped = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user = relationship("User", back_populates="transactions")
    merchant = relationship("DemoMerchant", back_populates="transactions")
    events = relationship("PaymentEvent", back_populates="transaction", order_by="PaymentEvent.event_timestamp.asc()", cascade="all, delete-orphan")
    resolution_case = relationship("ResolutionCase", back_populates="transaction", uselist=False)
    provider_observations = relationship("ProviderObservation", back_populates="transaction", cascade="all, delete-orphan")


class PaymentEvent(Base):
    __tablename__ = "payment_events"

    id = Column(String(64), primary_key=True, default=lambda: f"ev_{uuid.uuid4().hex[:12]}")
    transaction_id = Column(String(64), ForeignKey("transactions.id"), nullable=False, index=True)
    
    # Event types:
    # INITIATED, DEBIT_REPORTED, GATEWAY_PROCESSING, BENEFICIARY_PENDING,
    # BENEFICIARY_CONFIRMED, PAYMENT_FAILED, REVERSAL_INITIATED, REVERSAL_COMPLETED
    event_type = Column(String(50), nullable=False)
    
    # Source: RAZORPAY_SANDBOX, SIMULATED_PAYER_BANK, SIMULATED_BENEFICIARY_BANK,
    # DEMO_MERCHANT, NPCI_UPI_GATEWAY, PROVIDER_WEBHOOK
    source = Column(String(60), nullable=False)
    
    provider_reference = Column(String(100), nullable=True)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    
    # Verification: VERIFIED, UNVERIFIED, REJECTED
    verification_status = Column(String(30), default="VERIFIED")
    
    is_synthetic = Column(Boolean, default=True)
    evidence_payload = Column(Text, default="{}")  # JSON string
    
    event_timestamp = Column(DateTime(timezone=True), default=utcnow)
    recorded_at = Column(DateTime(timezone=True), default=utcnow)

    transaction = relationship("Transaction", back_populates="events")

    def get_payload(self):
        try:
            return json.loads(self.evidence_payload) if self.evidence_payload else {}
        except Exception:
            return {}


class ProviderObservation(Base):
    __tablename__ = "provider_observations"

    id = Column(String(64), primary_key=True, default=lambda: f"obs_{uuid.uuid4().hex[:12]}")
    transaction_id = Column(String(64), ForeignKey("transactions.id"), nullable=False, index=True)
    provider = Column(String(50), nullable=False)
    observed_status = Column(String(50), nullable=False)
    response_payload = Column(Text, default="{}")
    latency_ms = Column(Float, default=0.0)
    observed_at = Column(DateTime(timezone=True), default=utcnow)

    transaction = relationship("Transaction", back_populates="provider_observations")
