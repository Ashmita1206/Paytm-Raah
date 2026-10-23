from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel
from app.schemas.payment import AIActionOut

class ResolutionCaseOut(BaseModel):
    id: str
    case_number: str
    transaction_id: str
    user_id: str
    status: str
    category: str
    policy_name: str
    regulatory_deadline: Optional[datetime]
    policy_explanation: Optional[str]
    compensation_eligible: bool
    compensation_rate_inr: float
    assigned_agent: str
    latest_ai_action: str
    last_checked_at: Optional[datetime]
    next_check_at: Optional[datetime]
    retry_count: int
    correlated_incident_id: Optional[str]
    resolution_summary: Optional[str]
    created_at: datetime
    updated_at: datetime
    action_logs: Optional[List[AIActionOut]] = []

class FollowupTriggerRequest(BaseModel):
    reason: Optional[str] = "Manual autonomous recheck triggered"

class EscalateCaseRequest(BaseModel):
    reason: str
    requested_by: Optional[str] = "CUSTOMER"
