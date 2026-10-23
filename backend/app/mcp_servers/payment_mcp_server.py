import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from mcp.server.mcpserver import MCPServer
from sqlalchemy.orm import Session
from app.database.session import SessionLocal
from app.models.payment import Transaction, PaymentEvent, ProviderObservation
from app.models.case import ResolutionCase, CaseActionLog, ScheduledFollowup, HumanApprovalRequest
from app.models.notification import Notification
from app.models.user import DemoMerchant
from app.policies.reversal_policy import RegulatoryPolicyEngine
from app.utils.time_utils import utcnow, ensure_naive

# Instantiate the official MCP Server for RAAH Payment Intelligence
mcp_server = MCPServer("raah-payment-intelligence")

@mcp_server.tool()
def get_transaction_status(transaction_id: str) -> str:
    """
    Retrieve the authoritative, evidence-backed status of a transaction.
    Returns status, amount, merchant details, bank, and latest verification evidence.
    """
    db: Session = SessionLocal()
    try:
        tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()
        if not tx:
            return json.dumps({"error": f"Transaction {transaction_id} not found", "found": False})
        
        merchant = db.query(DemoMerchant).filter(DemoMerchant.id == tx.merchant_id).first()
        return json.dumps({
            "found": True,
            "transaction_id": tx.id,
            "status": tx.status,
            "amount": tx.amount,
            "currency": tx.currency,
            "merchant_id": tx.merchant_id,
            "merchant_name": merchant.merchant_name if merchant else "Unknown Merchant",
            "payer_bank": tx.payer_bank,
            "beneficiary_bank": tx.beneficiary_bank,
            "error_code": tx.error_code,
            "failure_reason": tx.failure_reason,
            "is_synthetic": tx.is_synthetic,
            "created_at": tx.created_at.isoformat() if tx.created_at else None,
            "updated_at": tx.updated_at.isoformat() if tx.updated_at else None
        })
    finally:
        db.close()


@mcp_server.tool()
def get_payment_events(transaction_id: str) -> str:
    """
    Retrieve all verified and unverified chronological events recorded for a transaction.
    Forms Timeline A (Money Journey).
    """
    db: Session = SessionLocal()
    try:
        events = db.query(PaymentEvent).filter(PaymentEvent.transaction_id == transaction_id).order_by(PaymentEvent.event_timestamp.asc()).all()
        results = []
        for ev in events:
            results.append({
                "id": ev.id,
                "event_type": ev.event_type,
                "source": ev.source,
                "title": ev.title,
                "description": ev.description,
                "verification_status": ev.verification_status,
                "is_synthetic": ev.is_synthetic,
                "event_timestamp": ev.event_timestamp.isoformat() if ev.event_timestamp else None
            })
        return json.dumps({"transaction_id": transaction_id, "event_count": len(results), "events": results})
    finally:
        db.close()


@mcp_server.tool()
def get_merchant_confirmation(transaction_id: str) -> str:
    """
    Queries the beneficiary merchant backend to verify if order settlement / fulfillment confirmation was recorded.
    """
    db: Session = SessionLocal()
    try:
        tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()
        if not tx:
            return json.dumps({"found": False, "confirmed": False, "reason": "Transaction not found"})
        
        # Check if any event has source DEMO_MERCHANT and status BENEFICIARY_CONFIRMED
        confirm_event = db.query(PaymentEvent).filter(
            PaymentEvent.transaction_id == transaction_id,
            PaymentEvent.source == "DEMO_MERCHANT",
            PaymentEvent.event_type == "BENEFICIARY_CONFIRMED"
        ).first()

        if confirm_event:
            return json.dumps({
                "found": True,
                "merchant_confirmed": True,
                "confirmation_reference": confirm_event.provider_reference or "MERCH-ACK-OK",
                "verified_at": confirm_event.event_timestamp.isoformat() if confirm_event.event_timestamp else None
            })
        else:
            return json.dumps({
                "found": True,
                "merchant_confirmed": False,
                "status": "AWAITING_SETTLEMENT_OR_TIMEOUT",
                "reason": "Merchant terminal reports no payment notification received from switch"
            })
    finally:
        db.close()


@mcp_server.tool()
def get_reversal_status(transaction_id: str) -> str:
    """
    Queries the payer bank and switch to determine if an automatic reversal has been initiated or credited.
    """
    db: Session = SessionLocal()
    try:
        rev_initiated = db.query(PaymentEvent).filter(
            PaymentEvent.transaction_id == transaction_id,
            PaymentEvent.event_type == "REVERSAL_INITIATED"
        ).first()

        rev_completed = db.query(PaymentEvent).filter(
            PaymentEvent.transaction_id == transaction_id,
            PaymentEvent.event_type == "REVERSAL_COMPLETED"
        ).first()

        if rev_completed:
            return json.dumps({
                "reversal_state": "COMPLETED",
                "details": "Refund credited to payer bank account",
                "rrn": rev_completed.provider_reference or "RRN-REV-CREDIT",
                "credited_at": rev_completed.event_timestamp.isoformat() if rev_completed.event_timestamp else None
            })
        elif rev_initiated:
            return json.dumps({
                "reversal_state": "INITIATED_PENDING",
                "details": "Reversal batch transmitted by switch to payer bank; credit confirmation pending",
                "initiated_at": rev_initiated.event_timestamp.isoformat() if rev_initiated.event_timestamp else None
            })
        else:
            return json.dumps({
                "reversal_state": "NOT_INITIATED",
                "details": "No reversal event registered across switch or payer bank"
            })
    finally:
        db.close()


@mcp_server.tool()
def get_applicable_reversal_policy(category: str) -> str:
    """
    Deterministic evaluation of applicable regulatory reversal policy and TAT rules (e.g. RBI Harmonisation T+5 or T+1).
    """
    res = RegulatoryPolicyEngine.evaluate_transaction(category, utcnow())
    return json.dumps(res, default=str)


@mcp_server.tool()
def create_resolution_case(transaction_id: str, reason: str) -> str:
    """
    Authorized state-changing tool: Creates a persistent Resolution Case for an uncertain transaction.
    Enforces idempotency: does not duplicate case if one already exists for this transaction.
    """
    db: Session = SessionLocal()
    try:
        tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()
        if not tx:
            return json.dumps({"success": False, "error": f"Transaction {transaction_id} not found"})
        
        # Idempotency check: see if case already exists
        existing_case = db.query(ResolutionCase).filter(ResolutionCase.transaction_id == transaction_id).first()
        if existing_case:
            return json.dumps({
                "success": True,
                "already_exists": True,
                "case_id": existing_case.id,
                "case_number": existing_case.case_number,
                "status": existing_case.status,
                "message": "Resolution case already active"
            })

        # Evaluate applicable regulatory policy
        category = "UPI_P2M"
        policy_eval = RegulatoryPolicyEngine.evaluate_transaction(category, tx.created_at or utcnow())
        
        case_num = f"CASE-2026-{uuid.uuid4().hex[:6].upper()}"
        new_case = ResolutionCase(
            case_number=case_num,
            transaction_id=tx.id,
            user_id=tx.user_id,
            status="INVESTIGATING",
            category=category,
            policy_name=policy_eval["policy_name"],
            regulatory_deadline=policy_eval["regulatory_deadline"],
            policy_explanation=policy_eval["disclaimer"],
            assigned_agent="RAAH_RESCUE",
            latest_ai_action=f"Case created: {reason}",
            next_check_at=utcnow() + timedelta(minutes=10)
        )
        db.add(new_case)
        db.flush()

        # Audit log the case creation
        log = CaseActionLog(
            case_id=new_case.id,
            agent_type="RAAH_RESCUE",
            tool_invoked="create_resolution_case",
            action_title="Resolution Case Registered",
            action_description=f"Proactive autonomous recovery case created. Reason: {reason}",
            input_payload=json.dumps({"transaction_id": transaction_id, "reason": reason}),
            output_payload=json.dumps({"case_number": case_num, "deadline": policy_eval["regulatory_deadline_iso"]}),
            validation_outcome="VALIDATED",
            execution_outcome="SUCCESS"
        )
        db.add(log)
        db.commit()

        return json.dumps({
            "success": True,
            "case_id": new_case.id,
            "case_number": new_case.case_number,
            "status": new_case.status,
            "policy_name": new_case.policy_name,
            "regulatory_deadline": policy_eval["regulatory_deadline_text"]
        })
    finally:
        db.close()


@mcp_server.tool()
def update_resolution_case(case_id: str, new_status: str, notes: str) -> str:
    """
    Authorized state-changing tool: Updates status and notes of a Resolution Case with audit logging.
    """
    db: Session = SessionLocal()
    try:
        case = db.query(ResolutionCase).filter(ResolutionCase.id == case_id).first()
        if not case:
            return json.dumps({"success": False, "error": f"Case {case_id} not found"})

        old_status = case.status
        case.status = new_status
        case.latest_ai_action = notes
        case.last_checked_at = utcnow()
        case.updated_at = utcnow()

        # Audit log
        log = CaseActionLog(
            case_id=case.id,
            agent_type="RAAH_RESCUE",
            tool_invoked="update_resolution_case",
            action_title=f"Case Status Transition ({old_status} -> {new_status})",
            action_description=notes,
            input_payload=json.dumps({"case_id": case_id, "new_status": new_status, "notes": notes}),
            output_payload=json.dumps({"previous_status": old_status, "current_status": new_status}),
            validation_outcome="VALIDATED",
            execution_outcome="SUCCESS"
        )
        db.add(log)
        db.commit()

        return json.dumps({
            "success": True,
            "case_id": case.id,
            "case_number": case.case_number,
            "status": case.status,
            "notes": notes
        })
    finally:
        db.close()


@mcp_server.tool()
def schedule_case_followup(case_id: str, delay_seconds: int, action_type: str) -> str:
    """
    Authorized tool: Schedules a persistent background follow-up check for autonomous verification.
    """
    db: Session = SessionLocal()
    try:
        case = db.query(ResolutionCase).filter(ResolutionCase.id == case_id).first()
        if not case:
            return json.dumps({"success": False, "error": f"Case {case_id} not found"})

        sched_time = utcnow() + timedelta(seconds=max(5, delay_seconds))
        followup = ScheduledFollowup(
            case_id=case.id,
            scheduled_for=sched_time,
            status="PENDING",
            action_type=action_type,
            retry_backoff_seconds=delay_seconds * 2
        )
        case.next_check_at = sched_time
        db.add(followup)

        # Audit log
        log = CaseActionLog(
            case_id=case.id,
            agent_type="RAAH_RESCUE",
            tool_invoked="schedule_case_followup",
            action_title="Autonomous Follow-up Scheduled",
            action_description=f"Background check scheduled for {sched_time.strftime('%I:%M:%S %p UTC')}. Type: {action_type}",
            input_payload=json.dumps({"case_id": case_id, "delay_seconds": delay_seconds, "action_type": action_type}),
            output_payload=json.dumps({"followup_id": followup.id, "scheduled_for": sched_time.isoformat()}),
            validation_outcome="VALIDATED",
            execution_outcome="SUCCESS"
        )
        db.add(log)
        db.commit()

        return json.dumps({
            "success": True,
            "followup_id": followup.id,
            "scheduled_for": sched_time.isoformat(),
            "action_type": action_type
        })
    finally:
        db.close()


@mcp_server.tool()
def request_human_review(case_id: str, reason: str) -> str:
    """
    Authorized tool: Requests human operations review when an autonomous threshold is reached.
    """
    db: Session = SessionLocal()
    try:
        case = db.query(ResolutionCase).filter(ResolutionCase.id == case_id).first()
        if not case:
            return json.dumps({"success": False, "error": f"Case {case_id} not found"})

        req = HumanApprovalRequest(
            case_id=case.id,
            action_name="ESCALATE_TO_BANK_OPERATIONS",
            description=reason,
            status="PENDING",
            requested_by="RAAH_RESCUE"
        )
        case.status = "ESCALATED"
        case.latest_ai_action = f"Escalated to human operations: {reason}"
        db.add(req)

        # Audit log
        log = CaseActionLog(
            case_id=case.id,
            agent_type="RAAH_RESCUE",
            tool_invoked="request_human_review",
            action_title="Human Operations Review Requested",
            action_description=reason,
            input_payload=json.dumps({"case_id": case_id, "reason": reason}),
            output_payload=json.dumps({"request_id": req.id, "status": "PENDING"}),
            validation_outcome="VALIDATED",
            execution_outcome="SUCCESS"
        )
        db.add(log)
        db.commit()

        return json.dumps({
            "success": True,
            "approval_request_id": req.id,
            "status": "PENDING",
            "message": "Human review queued"
        })
    finally:
        db.close()


@mcp_server.tool()
def send_case_notification(user_id: str, title: str, message: str) -> str:
    """
    Sends an in-app notification to the customer regarding recovery progress.
    """
    db: Session = SessionLocal()
    try:
        notif = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type="CASE_UPDATE",
            read=False
        )
        db.add(notif)
        db.commit()
        return json.dumps({"success": True, "notification_id": notif.id})
    finally:
        db.close()
