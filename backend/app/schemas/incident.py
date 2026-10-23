from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

class IncidentLinkOut(BaseModel):
    id: str
    transaction_id: str
    case_id: Optional[str]
    correlation_confidence: float
    linked_at: datetime
    transaction_amount: Optional[float] = None
    merchant_name: Optional[str] = None
    payer_bank: Optional[str] = None

class IncidentOut(BaseModel):
    id: str
    incident_number: str
    title: str
    error_category: str
    provider: str
    bank: str
    affected_count: int
    baseline_failure_rate: float
    observed_failure_rate: float
    status: str
    summary: Optional[str]
    recommended_mitigation: Optional[str]
    ai_actions_taken: Optional[List[str]] = []
    detected_at: datetime
    resolved_at: Optional[datetime]
    linked_cases: Optional[List[IncidentLinkOut]] = []

class IncidentReviewRequest(BaseModel):
    action: str  # MITIGATE, BROADCAST_ADVISORY, RESOLVE, ESCALATE
    notes: Optional[str] = None
    reviewer_role: Optional[str] = "OPERATIONS_LEAD"

class SystemHealthOut(BaseModel):
    system_status: str  # HEALTHY, DEGRADED, INCIDENT_ACTIVE
    overall_success_rate: float
    active_incidents_count: int
    correlated_cases_count: int
    monitored_banks: List[dict]
