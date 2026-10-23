import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.incident import IncidentRecord, IncidentTransactionLink
from app.models.payment import Transaction
from app.models.case import ResolutionCase
from app.models.user import DemoMerchant
from app.schemas.incident import IncidentOut, IncidentLinkOut, IncidentReviewRequest, SystemHealthOut
from app.agents.pulse_agent import RaahPulseAgent

router = APIRouter(prefix="/incidents", tags=["Raah Pulse (Operations)"])

@router.get("/health", response_model=SystemHealthOut)
def get_system_health(db: Session = Depends(get_db)):
    """Provides operational payment health telemetry across monitored banks."""
    active_incs = db.query(IncidentRecord).filter(
        IncidentRecord.status.in_(["DETECTED", "INVESTIGATING", "CORRELATED"])
    ).all()

    total_links = db.query(IncidentTransactionLink).count()

    # Calculate overall success rate
    total_tx = db.query(Transaction).count()
    success_tx = db.query(Transaction).filter(Transaction.status == "SUCCESS").count()
    rate = round((success_tx / max(total_tx, 1)) * 100, 1)

    banks_monitored = [
        {"bank": "HDFC Bank", "status": "DEGRADED" if any(i.bank == "HDFC Bank" for i in active_incs) else "HEALTHY", "observed_latency_ms": 340},
        {"bank": "ICICI Bank", "status": "HEALTHY", "observed_latency_ms": 110},
        {"bank": "State Bank of India", "status": "HEALTHY", "observed_latency_ms": 135},
        {"bank": "Axis Bank", "status": "HEALTHY", "observed_latency_ms": 120}
    ]

    sys_status = "INCIDENT_ACTIVE" if active_incs else "HEALTHY"

    return SystemHealthOut(
        system_status=sys_status,
        overall_success_rate=rate,
        active_incidents_count=len(active_incs),
        correlated_cases_count=total_links,
        monitored_banks=banks_monitored
    )


@router.get("", response_model=List[IncidentOut])
def list_incidents(db: Session = Depends(get_db)):
    """List operational incidents detected by Raah Pulse."""
    incs = db.query(IncidentRecord).order_by(IncidentRecord.detected_at.desc()).all()
    results = []
    for inc in incs:
        actions = []
        try:
            actions = json.loads(inc.ai_actions_taken) if inc.ai_actions_taken else []
        except Exception:
            pass

        results.append(IncidentOut(
            id=inc.id,
            incident_number=inc.incident_number,
            title=inc.title,
            error_category=inc.error_category,
            provider=inc.provider,
            bank=inc.bank,
            affected_count=inc.affected_count,
            baseline_failure_rate=inc.baseline_failure_rate,
            observed_failure_rate=inc.observed_failure_rate,
            status=inc.status,
            summary=inc.summary,
            recommended_mitigation=inc.recommended_mitigation,
            ai_actions_taken=actions,
            detected_at=inc.detected_at,
            resolved_at=inc.resolved_at
        ))
    return results


@router.get("/{incident_id}", response_model=IncidentOut)
def get_incident(incident_id: str, db: Session = Depends(get_db)):
    inc = db.query(IncidentRecord).filter(
        (IncidentRecord.id == incident_id) | (IncidentRecord.incident_number == incident_id)
    ).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    actions = []
    try:
        actions = json.loads(inc.ai_actions_taken) if inc.ai_actions_taken else []
    except Exception:
        pass

    links = db.query(IncidentTransactionLink).filter(IncidentTransactionLink.incident_id == inc.id).all()
    link_outs = []
    for l in links:
        tx = db.query(Transaction).filter(Transaction.id == l.transaction_id).first()
        merch = db.query(DemoMerchant).filter(DemoMerchant.id == tx.merchant_id).first() if tx else None
        link_outs.append(IncidentLinkOut(
            id=l.id,
            transaction_id=l.transaction_id,
            case_id=l.case_id,
            correlation_confidence=l.correlation_confidence,
            linked_at=l.linked_at,
            transaction_amount=tx.amount if tx else None,
            merchant_name=merch.merchant_name if merch else "Merchant",
            payer_bank=tx.payer_bank if tx else None
        ))

    return IncidentOut(
        id=inc.id,
        incident_number=inc.incident_number,
        title=inc.title,
        error_category=inc.error_category,
        provider=inc.provider,
        bank=inc.bank,
        affected_count=inc.affected_count,
        baseline_failure_rate=inc.baseline_failure_rate,
        observed_failure_rate=inc.observed_failure_rate,
        status=inc.status,
        summary=inc.summary,
        recommended_mitigation=inc.recommended_mitigation,
        ai_actions_taken=actions,
        detected_at=inc.detected_at,
        resolved_at=inc.resolved_at,
        linked_cases=link_outs
    )


@router.get("/{incident_id}/linked-cases", response_model=List[IncidentLinkOut])
def get_linked_cases(incident_id: str, db: Session = Depends(get_db)):
    inc = db.query(IncidentRecord).filter(
        (IncidentRecord.id == incident_id) | (IncidentRecord.incident_number == incident_id)
    ).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    links = db.query(IncidentTransactionLink).filter(IncidentTransactionLink.incident_id == inc.id).all()
    results = []
    for l in links:
        tx = db.query(Transaction).filter(Transaction.id == l.transaction_id).first()
        merch = db.query(DemoMerchant).filter(DemoMerchant.id == tx.merchant_id).first() if tx else None
        results.append(IncidentLinkOut(
            id=l.id,
            transaction_id=l.transaction_id,
            case_id=l.case_id,
            correlation_confidence=l.correlation_confidence,
            linked_at=l.linked_at,
            transaction_amount=tx.amount if tx else None,
            merchant_name=merch.merchant_name if merch else None,
            payer_bank=tx.payer_bank if tx else None
        ))
    return results


@router.post("/{incident_id}/review")
async def review_incident(incident_id: str, payload: IncidentReviewRequest):
    """Executes operational action (MITIGATE, BROADCAST_ADVISORY, RESOLVE)."""
    res = await RaahPulseAgent.review_incident(incident_id, payload.action, payload.notes)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res
