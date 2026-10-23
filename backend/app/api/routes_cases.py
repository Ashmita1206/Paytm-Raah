from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.case import ResolutionCase, CaseActionLog, HumanApprovalRequest
from app.schemas.case import ResolutionCaseOut, FollowupTriggerRequest, EscalateCaseRequest
from app.schemas.payment import AIActionOut
from app.agents.rescue_agent import run_rescue_investigation
from app.utils.time_utils import utcnow, ensure_naive

router = APIRouter(prefix="/cases", tags=["Recovery Cases"])

@router.get("/{case_id}", response_model=ResolutionCaseOut)
def get_case(case_id: str, db: Session = Depends(get_db)):
    case = db.query(ResolutionCase).filter(
        (ResolutionCase.id == case_id) | (ResolutionCase.case_number == case_id)
    ).first()
    if not case:
        raise HTTPException(status_code=404, detail="Resolution case not found")

    actions = db.query(CaseActionLog).filter(
        CaseActionLog.case_id == case.id
    ).order_by(CaseActionLog.created_at.asc()).all()

    action_outs = [
        AIActionOut(
            id=a.id,
            agent_type=a.agent_type,
            tool_invoked=a.tool_invoked,
            action_title=a.action_title,
            action_description=a.action_description,
            validation_outcome=a.validation_outcome,
            execution_outcome=a.execution_outcome,
            created_at=a.created_at
        ) for a in actions
    ]

    return ResolutionCaseOut(
        id=case.id,
        case_number=case.case_number,
        transaction_id=case.transaction_id,
        user_id=case.user_id,
        status=case.status,
        category=case.category,
        policy_name=case.policy_name,
        regulatory_deadline=case.regulatory_deadline,
        policy_explanation=case.policy_explanation,
        compensation_eligible=case.compensation_eligible,
        compensation_rate_inr=case.compensation_rate_inr,
        assigned_agent=case.assigned_agent,
        latest_ai_action=case.latest_ai_action,
        last_checked_at=case.last_checked_at,
        next_check_at=case.next_check_at,
        retry_count=case.retry_count or 0,
        correlated_incident_id=case.correlated_incident_id,
        resolution_summary=case.resolution_summary,
        created_at=case.created_at,
        updated_at=case.updated_at,
        action_logs=action_outs
    )


@router.get("/{case_id}/actions", response_model=List[AIActionOut])
def get_case_actions(case_id: str, db: Session = Depends(get_db)):
    case = db.query(ResolutionCase).filter(
        (ResolutionCase.id == case_id) | (ResolutionCase.case_number == case_id)
    ).first()
    if not case:
        raise HTTPException(status_code=404, detail="Resolution case not found")

    actions = db.query(CaseActionLog).filter(
        CaseActionLog.case_id == case.id
    ).order_by(CaseActionLog.created_at.asc()).all()

    return [
        AIActionOut(
            id=a.id,
            agent_type=a.agent_type,
            tool_invoked=a.tool_invoked,
            action_title=a.action_title,
            action_description=a.action_description,
            validation_outcome=a.validation_outcome,
            execution_outcome=a.execution_outcome,
            created_at=a.created_at
        ) for a in actions
    ]


@router.post("/{case_id}/followup")
async def trigger_case_followup(case_id: str, payload: FollowupTriggerRequest, db: Session = Depends(get_db)):
    """Triggers an immediate autonomous recheck for this case via LangGraph agent."""
    case = db.query(ResolutionCase).filter(
        (ResolutionCase.id == case_id) | (ResolutionCase.case_number == case_id)
    ).first()
    if not case:
        raise HTTPException(status_code=404, detail="Resolution case not found")

    case.retry_count = (case.retry_count or 0) + 1
    case.last_checked_at = utcnow()
    db.commit()

    res = await run_rescue_investigation(case.transaction_id, case.user_id)
    return {
        "success": True,
        "case_number": case.case_number,
        "status": case.status,
        "result_summary": res.get("status_summary")
    }


@router.post("/{case_id}/escalate")
def escalate_case(case_id: str, payload: EscalateCaseRequest, db: Session = Depends(get_db)):
    case = db.query(ResolutionCase).filter(
        (ResolutionCase.id == case_id) | (ResolutionCase.case_number == case_id)
    ).first()
    if not case:
        raise HTTPException(status_code=404, detail="Resolution case not found")

    case.status = "ESCALATED"
    case.latest_ai_action = f"Escalated: {payload.reason}"
    
    req = HumanApprovalRequest(
        case_id=case.id,
        action_name="MANUAL_BANK_RECONCILIATION",
        description=payload.reason,
        status="PENDING",
        requested_by=payload.requested_by or "CUSTOMER"
    )
    db.add(req)
    db.commit()

    return {
        "success": True,
        "case_number": case.case_number,
        "status": case.status,
        "approval_request_id": req.id
    }
