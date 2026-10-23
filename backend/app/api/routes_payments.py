import uuid
import json
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.payment import Transaction, PaymentEvent, ProviderObservation
from app.models.case import ResolutionCase, CaseActionLog
from app.models.user import DemoMerchant, MerchantOrder
from app.models.incident import IncidentRecord
from app.schemas.payment import (
    CreateTestOrderRequest, CreateOrderResponse, PaymentEventOut,
    AIActionOut, RescueCardInfo, PaymentJourneyResponse,
    VerifyPaymentRequest, TransactionDetail
)
from app.services.retryguard_service import RetryGuardService
from app.policies.reversal_policy import RegulatoryPolicyEngine
from app.agents.rescue_agent import run_rescue_investigation
from app.utils.time_utils import utcnow, ensure_naive

router = APIRouter(prefix="/payments", tags=["Payments"])

@router.post("/test-order", response_model=CreateOrderResponse)
async def create_test_order(payload: CreateTestOrderRequest, db: Session = Depends(get_db)):
    """
    Creates a supported test or simulated payment order.
    Enforces RetryGuard duplicate-payment check unless acknowledged.
    """
    merchant = db.query(DemoMerchant).filter(DemoMerchant.id == payload.merchant_id).first()
    if not merchant:
        raise HTTPException(status_code=404, detail="Demo merchant not found")

    # RetryGuard check
    if not payload.acknowledged_duplicate:
        dup_check = RetryGuardService.check_duplicate_risk(
            db=db,
            user_id=payload.user_id or "user_default_01",
            merchant_id=payload.merchant_id,
            amount=payload.amount,
            window_minutes=15
        )
        if dup_check["has_potential_duplicate"]:
            raise HTTPException(
                status_code=409,
                detail={
                    "message": dup_check["warning_message"],
                    "existing_transaction_id": dup_check["existing_transaction_id"],
                    "requires_acknowledgement": True
                }
            )

    now = utcnow()
    order_id = f"order_{uuid.uuid4().hex[:10]}"
    tx_id = f"tx_{uuid.uuid4().hex[:10]}"

    # Check scenario override
    status = "OUTCOME_UNKNOWN"
    err_code = "E_BENEFICIARY_TIMEOUT"
    fail_reason = "Debit reported by payer bank; merchant confirmation missing."

    if payload.force_scenario == "SUCCESS":
        status = "SUCCESS"
        err_code = None
        fail_reason = None
    elif payload.force_scenario == "FAILED":
        status = "FAILED"
        err_code = "E_PAYER_AUTHENTICATION_FAILED"
        fail_reason = "Payment rejected prior to debit."

    tx = Transaction(
        id=tx_id,
        user_id=payload.user_id or "user_default_01",
        merchant_id=payload.merchant_id,
        amount=payload.amount,
        currency="INR",
        status=status,
        provider="UPI_SIMULATOR",
        upi_ref_no=f"UPI-2026-{uuid.uuid4().hex[:8].upper()}",
        idempotency_key=payload.idempotency_key or f"idemp_{uuid.uuid4().hex[:8]}",
        payer_bank="HDFC Bank",
        beneficiary_bank="ICICI Bank",
        gateway="NPCI_UPI_SWITCH",
        error_code=err_code,
        failure_reason=fail_reason,
        is_synthetic=True,
        created_at=now
    )
    db.add(tx)

    # Initial payment events
    ev_init = PaymentEvent(
        transaction_id=tx.id,
        event_type="INITIATED",
        source="UPI_CLIENT",
        title="Payment Initiated (DEMO / SIMULATED)",
        description=f"Payment instruction of ₹{payload.amount:,.2f} transmitted to NPCI switch.",
        verification_status="VERIFIED",
        is_synthetic=True,
        event_timestamp=now
    )
    db.add(ev_init)

    if status in ("OUTCOME_UNKNOWN", "SUCCESS"):
        ev_debit = PaymentEvent(
            transaction_id=tx.id,
            event_type="DEBIT_REPORTED",
            source="SIMULATED_PAYER_BANK",
            title="Payer Debited (DEMO / SIMULATED)",
            description=f"HDFC Bank reported account debited for ₹{payload.amount:,.2f}.",
            verification_status="VERIFIED",
            is_synthetic=True,
            event_timestamp=now
        )
        db.add(ev_debit)

    if status == "OUTCOME_UNKNOWN":
        ev_miss = PaymentEvent(
            transaction_id=tx.id,
            event_type="BENEFICIARY_PENDING",
            source="DEMO_MERCHANT",
            title="Beneficiary Confirmation Missing (DEMO / SIMULATED)",
            description="Merchant POS timed out awaiting credit push signal from switch.",
            verification_status="UNVERIFIED",
            is_synthetic=True,
            event_timestamp=now
        )
        db.add(ev_miss)

    db.commit()

    # If outcome is unknown, immediately launch Raah Rescue LangGraph investigation
    if status == "OUTCOME_UNKNOWN":
        await run_rescue_investigation(tx.id, tx.user_id)

    return CreateOrderResponse(
        transaction_id=tx.id,
        order_id=order_id,
        amount=tx.amount,
        currency=tx.currency,
        merchant_name=merchant.merchant_name,
        upi_vpa=merchant.upi_vpa,
        status=tx.status,
        is_synthetic=True
    )


@router.get("/list", response_model=List[TransactionDetail])
def list_transactions(limit: int = 20, db: Session = Depends(get_db)):
    """Returns recent transactions with merchant and case details."""
    txs = db.query(Transaction).order_by(Transaction.created_at.desc()).limit(limit).all()
    results = []
    for t in txs:
        merch = db.query(DemoMerchant).filter(DemoMerchant.id == t.merchant_id).first()
        case = db.query(ResolutionCase).filter(ResolutionCase.transaction_id == t.id).first()
        results.append(TransactionDetail(
            id=t.id,
            user_id=t.user_id,
            merchant_id=t.merchant_id,
            merchant_name=merch.merchant_name if merch else "Unknown Merchant",
            merchant_vpa=merch.upi_vpa if merch else "unknown@upi",
            amount=t.amount,
            currency=t.currency,
            status=t.status,
            upi_ref_no=t.upi_ref_no,
            error_code=t.error_code,
            failure_reason=t.failure_reason,
            payer_bank=t.payer_bank or "HDFC Bank",
            beneficiary_bank=t.beneficiary_bank or "ICICI Bank",
            is_synthetic=t.is_synthetic,
            created_at=t.created_at,
            case_number=case.case_number if case else None
        ))
    return results


@router.get("/{tx_id}", response_model=TransactionDetail)
def get_transaction(tx_id: str, db: Session = Depends(get_db)):
    tx = db.query(Transaction).filter(Transaction.id == tx_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    merch = db.query(DemoMerchant).filter(DemoMerchant.id == tx.merchant_id).first()
    case = db.query(ResolutionCase).filter(ResolutionCase.transaction_id == tx.id).first()
    return TransactionDetail(
        id=tx.id,
        user_id=tx.user_id,
        merchant_id=tx.merchant_id,
        merchant_name=merch.merchant_name if merch else "Unknown Merchant",
        merchant_vpa=merch.upi_vpa if merch else "unknown@upi",
        amount=tx.amount,
        currency=tx.currency,
        status=tx.status,
        upi_ref_no=tx.upi_ref_no,
        error_code=tx.error_code,
        failure_reason=tx.failure_reason,
        payer_bank=tx.payer_bank or "HDFC Bank",
        beneficiary_bank=tx.beneficiary_bank or "ICICI Bank",
        is_synthetic=tx.is_synthetic,
        created_at=tx.created_at,
        case_number=case.case_number if case else None
    )


@router.get("/{tx_id}/journey", response_model=PaymentJourneyResponse)
def get_payment_journey(tx_id: str, db: Session = Depends(get_db)):
    """
    FLAGSHIP ENDPOINT:
    Returns the two distinct timelines:
    - Timeline A: Money Journey (Strictly evidence-backed states)
    - Timeline B: AI Resolution Journey (Autonomous agent actions & tool executions)
    - Payment Rescue Information Card with regulatory turnaround & verified facts.
    """
    tx = db.query(Transaction).filter(Transaction.id == tx_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    merch = db.query(DemoMerchant).filter(DemoMerchant.id == tx.merchant_id).first()
    case = db.query(ResolutionCase).filter(ResolutionCase.transaction_id == tx.id).first()

    # Timeline A: Money Journey
    events = db.query(PaymentEvent).filter(
        PaymentEvent.transaction_id == tx.id
    ).order_by(PaymentEvent.event_timestamp.asc()).all()

    money_timeline = []
    for e in events:
        payload = {}
        try:
            payload = json.loads(e.evidence_payload) if e.evidence_payload else {}
        except Exception:
            pass
        money_timeline.append(PaymentEventOut(
            id=e.id,
            event_type=e.event_type,
            source=e.source,
            title=e.title,
            description=e.description,
            verification_status=e.verification_status,
            is_synthetic=e.is_synthetic,
            event_timestamp=e.event_timestamp,
            evidence_payload=payload
        ))

    # Timeline B: AI Resolution Journey
    ai_timeline = []
    correlated_inc_num = None
    if case:
        actions = db.query(CaseActionLog).filter(
            CaseActionLog.case_id == case.id
        ).order_by(CaseActionLog.created_at.asc()).all()
        for a in actions:
            ai_timeline.append(AIActionOut(
                id=a.id,
                agent_type=a.agent_type,
                tool_invoked=a.tool_invoked,
                action_title=a.action_title,
                action_description=a.action_description,
                validation_outcome=a.validation_outcome,
                execution_outcome=a.execution_outcome,
                created_at=a.created_at
            ))
        
        if case.correlated_incident_id:
            inc = db.query(IncidentRecord).filter(IncidentRecord.id == case.correlated_incident_id).first()
            if inc:
                correlated_inc_num = inc.incident_number

    # Calculate regulatory policy evaluation
    policy_eval = RegulatoryPolicyEngine.evaluate_transaction("UPI_P2M", tx.created_at)

    # Determine known evidence vs what remains unknown
    has_debit = any(e.event_type == "DEBIT_REPORTED" for e in events)
    has_merchant_confirm = any(e.event_type == "BENEFICIARY_CONFIRMED" for e in events)
    has_rev_completed = any(e.event_type == "REVERSAL_COMPLETED" for e in events)

    known_evidence = f"Payer account debited by {tx.payer_bank or 'HDFC Bank'}." if has_debit else "No debit reported by payer bank."
    if has_merchant_confirm:
        known_evidence += " Merchant POS confirmed credit."
    elif has_rev_completed:
        known_evidence += " Reversal refund confirmed credited to payer account."

    what_remains_unknown = "Merchant settlement acknowledgement missing from beneficiary switch." if not (has_merchant_confirm or has_rev_completed) else "All transaction phases verified."

    rescue_card = RescueCardInfo(
        transaction_id=tx.id,
        case_number=case.case_number if case else None,
        amount=tx.amount,
        merchant_name=merch.merchant_name if merch else "Unknown Merchant",
        merchant_category=merch.category if merch else "GROCERY",
        merchant_upi=merch.upi_vpa if merch else "unknown@upi",
        last_verified_status=tx.status,
        known_failure_evidence=known_evidence,
        what_remains_unknown=what_remains_unknown,
        regulatory_deadline_title="RBI Failed-Transaction Turnaround (TAT)",
        regulatory_deadline_date=policy_eval["regulatory_deadline"],
        regulatory_explanation=policy_eval["disclaimer"],
        compensation_rate=f"₹{policy_eval['compensation_per_day_inr']:.0f}/day after regulatory TAT",
        last_checked_at=case.last_checked_at if case else tx.updated_at,
        next_scheduled_check=case.next_check_at if case else None,
        latest_ai_action=case.latest_ai_action if case else "Autonomous monitoring initialized",
        assigned_agent=case.assigned_agent if case else "RAAH_RESCUE",
        correlated_incident_number=correlated_inc_num
    )

    return PaymentJourneyResponse(
        transaction_id=tx.id,
        status=tx.status,
        amount=tx.amount,
        merchant_name=merch.merchant_name if merch else "Unknown Merchant",
        created_at=tx.created_at,
        rescue_card=rescue_card,
        money_journey=money_timeline,
        ai_resolution_journey=ai_timeline
    )


@router.post("/{tx_id}/verify")
async def verify_payment(tx_id: str, payload: VerifyPaymentRequest, db: Session = Depends(get_db)):
    """
    Simulates / verifies authoritative payment outcome.
    Demonstrates that client network interruptions do not fabricate a FAILED state.
    """
    tx = db.query(Transaction).filter(Transaction.id == tx_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if payload.simulate_network_drop:
        # Client lost connection: Server status remains authoritative OUTCOME_UNKNOWN or SUCCESS
        return {
            "status": tx.status,
            "message": "Client network dropped during receipt fetch. Authoritative server status maintained without marking FAILED.",
            "transaction_id": tx.id
        }

    # Trigger re-investigation
    res = await run_rescue_investigation(tx.id, tx.user_id)
    return {
        "status": tx.status,
        "investigation_result": res.get("status_summary"),
        "transaction_id": tx.id
    }
