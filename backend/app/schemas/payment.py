from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel

class CreateTestOrderRequest(BaseModel):
    merchant_id: str
    amount: float
    user_id: Optional[str] = "user_default_01"
    force_scenario: Optional[str] = None  # e.g. "SCENARIO_3", "SCENARIO_2"
    idempotency_key: Optional[str] = None
    acknowledged_duplicate: Optional[bool] = False

class CreateOrderResponse(BaseModel):
    transaction_id: str
    order_id: str
    amount: float
    currency: str
    merchant_name: str
    upi_vpa: str
    status: str
    razorpay_order_id: Optional[str] = None
    is_synthetic: bool = True

class PaymentEventOut(BaseModel):
    id: str
    event_type: str
    source: str
    title: str
    description: Optional[str]
    verification_status: str
    is_synthetic: bool
    event_timestamp: datetime
    evidence_payload: Optional[Dict[str, Any]] = None

class AIActionOut(BaseModel):
    id: str
    agent_type: str
    tool_invoked: str
    action_title: str
    action_description: Optional[str]
    validation_outcome: str
    execution_outcome: str
    created_at: datetime

class RescueCardInfo(BaseModel):
    transaction_id: str
    case_number: Optional[str]
    amount: float
    merchant_name: str
    merchant_category: str
    merchant_upi: str
    last_verified_status: str
    known_failure_evidence: str
    what_remains_unknown: str
    regulatory_deadline_title: str
    regulatory_deadline_date: Optional[datetime]
    regulatory_explanation: str
    compensation_rate: str
    last_checked_at: Optional[datetime]
    next_scheduled_check: Optional[datetime]
    latest_ai_action: str
    assigned_agent: str
    correlated_incident_number: Optional[str] = None

class PaymentJourneyResponse(BaseModel):
    transaction_id: str
    status: str
    amount: float
    merchant_name: str
    created_at: datetime
    rescue_card: RescueCardInfo
    money_journey: List[PaymentEventOut]
    ai_resolution_journey: List[AIActionOut]

class VerifyPaymentRequest(BaseModel):
    razorpay_payment_id: Optional[str] = None
    razorpay_order_id: Optional[str] = None
    razorpay_signature: Optional[str] = None
    simulate_network_drop: Optional[bool] = False

class TransactionDetail(BaseModel):
    id: str
    user_id: str
    merchant_id: str
    merchant_name: str
    merchant_vpa: str
    amount: float
    currency: str
    status: str
    upi_ref_no: Optional[str]
    error_code: Optional[str]
    failure_reason: Optional[str]
    payer_bank: str
    beneficiary_bank: str
    is_synthetic: bool
    created_at: datetime
    case_number: Optional[str] = None
