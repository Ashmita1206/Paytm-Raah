import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.database.session import SessionLocal
from app.models.user import User, DemoMerchant
from app.models.payment import Transaction, PaymentEvent
from app.models.case import ResolutionCase, CaseActionLog, ScheduledFollowup
from app.models.incident import IncidentRecord, IncidentTransactionLink
from app.agents.rescue_agent import run_rescue_investigation
from app.agents.pulse_agent import RaahPulseAgent
from app.policies.reversal_policy import RegulatoryPolicyEngine
from app.utils.time_utils import utcnow, ensure_naive

class ScenarioEngine:
    """
    Executes live synthetic payment scenarios against real database models and agents.
    Every generated event is strictly marked with is_synthetic=True and DEMO / SIMULATED.
    """

    SCENARIOS = {
        "1": {
            "name": "Payment Fails Before Debit",
            "desc": "Gateway rejects payment instruction (e.g. invalid PIN / expired session) prior to customer bank account debit.",
            "category": "PRE_DEBIT"
        },
        "2": {
            "name": "Payment Succeeds on Server, Client Response Lost",
            "desc": "Switch & merchant confirm settlement, but user's mobile connectivity dropped before receiving receipt.",
            "category": "DROPPED_CLIENT"
        },
        "3": {
            "name": "Debit Reported, Beneficiary Confirmation Missing",
            "desc": "Payer bank reports ₹4,000 debited, but merchant POS confirms no payment push received within timeout.",
            "category": "DEBIT_NO_CONFIRMATION"
        },
        "4": {
            "name": "Reversal Initiated, Credit Pending",
            "desc": "NPCI switch registers automated reversal batch; payer bank credit is in transit.",
            "category": "REVERSAL_INITIATED"
        },
        "5": {
            "name": "Verified Reversal Completion Event Arrives",
            "desc": "Payer bank acknowledges ₹4,000 refund credit to customer account.",
            "category": "REVERSAL_COMPLETED"
        },
        "6": {
            "name": "Cluster Spike on HDFC (Raah Pulse)",
            "desc": "Injects a burst of gateway timeout failures across HDFC UPI transactions, triggering Raah Pulse incident correlation.",
            "category": "PULSE_INCIDENT"
        },
        "7": {
            "name": "Customer Attempts Possible Duplicate Payment",
            "desc": "Simulates user trying to pay ₹4,000 to same merchant while previous payment is unresolved, triggering RetryGuard.",
            "category": "RETRYGUARD"
        },
        "8": {
            "name": "Case Becomes Overdue Under RBI Policy",
            "desc": "Simulates passage of time beyond RBI turnaround limit (T+5), triggering automated compensation check and escalation.",
            "category": "OVERDUE_POLICY"
        }
    }

    @classmethod
    async def trigger_scenario(cls, scenario_id: str, user_id: str = "user_default_01", merchant_id: str = "merch_grocery_01", amount: float = 4000.0) -> Dict[str, Any]:
        db: Session = SessionLocal()
        try:
            now = utcnow()
            s_id = str(scenario_id).strip()

            if s_id == "1":
                # SCENARIO 1: Payment fails before debit
                tx = Transaction(
                    id=f"tx_scen1_{uuid.uuid4().hex[:8]}",
                    user_id=user_id,
                    merchant_id=merchant_id,
                    amount=amount,
                    currency="INR",
                    status="FAILED",
                    provider="UPI_SIMULATOR",
                    upi_ref_no=f"UPI-2026-{uuid.uuid4().hex[:8].upper()}",
                    error_code="E_PAYER_AUTHENTICATION_FAILED",
                    failure_reason="Authentication failed prior to debit. No funds transferred.",
                    payer_bank="HDFC Bank",
                    beneficiary_bank="ICICI Bank",
                    is_synthetic=True,
                    created_at=now
                )
                db.add(tx)
                db.flush()

                ev1 = PaymentEvent(
                    transaction_id=tx.id,
                    event_type="INITIATED",
                    source="UPI_CLIENT",
                    title="Payment Initiated (DEMO / SIMULATED)",
                    description=f"Payment of ₹{amount:,.2f} initiated from mobile scanner.",
                    verification_status="VERIFIED",
                    is_synthetic=True,
                    event_timestamp=now
                )
                ev2 = PaymentEvent(
                    transaction_id=tx.id,
                    event_type="PAYMENT_FAILED",
                    source="SIMULATED_PAYER_BANK",
                    title="Pre-Debit Rejection (DEMO / SIMULATED)",
                    description="Payer bank rejected request before account debit: User authentication cancelled.",
                    verification_status="VERIFIED",
                    is_synthetic=True,
                    event_timestamp=now + timedelta(seconds=2)
                )
                db.add(ev1)
                db.add(ev2)
                db.commit()

                return {
                    "scenario": 1,
                    "title": "Payment Fails Before Debit",
                    "transaction_id": tx.id,
                    "status": "FAILED",
                    "outcome": "Pre-debit rejection verified. Customer may retry safely without duplicate risk."
                }

            elif s_id == "2":
                # SCENARIO 2: Payment succeeds on server, client response dropped
                tx = Transaction(
                    id=f"tx_scen2_{uuid.uuid4().hex[:8]}",
                    user_id=user_id,
                    merchant_id=merchant_id,
                    amount=amount,
                    currency="INR",
                    status="SUCCESS",
                    provider="UPI_SIMULATOR",
                    upi_ref_no=f"UPI-2026-{uuid.uuid4().hex[:8].upper()}",
                    client_response_dropped=True,
                    payer_bank="HDFC Bank",
                    beneficiary_bank="ICICI Bank",
                    is_synthetic=True,
                    created_at=now
                )
                db.add(tx)
                db.flush()

                ev1 = PaymentEvent(
                    transaction_id=tx.id,
                    event_type="INITIATED",
                    source="UPI_CLIENT",
                    title="Payment Initiated (DEMO / SIMULATED)",
                    description=f"Instruction transmitted for ₹{amount:,.2f}.",
                    verification_status="VERIFIED",
                    is_synthetic=True,
                    event_timestamp=now
                )
                ev2 = PaymentEvent(
                    transaction_id=tx.id,
                    event_type="DEBIT_REPORTED",
                    source="SIMULATED_PAYER_BANK",
                    title="Payer Debited (DEMO / SIMULATED)",
                    description="HDFC Bank reports account debited.",
                    verification_status="VERIFIED",
                    is_synthetic=True,
                    event_timestamp=now + timedelta(seconds=1)
                )
                ev3 = PaymentEvent(
                    transaction_id=tx.id,
                    event_type="BENEFICIARY_CONFIRMED",
                    source="DEMO_MERCHANT",
                    title="Merchant Settlement Confirmed (DEMO / SIMULATED)",
                    description="Merchant POS successfully settled. Client mobile missed server response.",
                    verification_status="VERIFIED",
                    is_synthetic=True,
                    event_timestamp=now + timedelta(seconds=3)
                )
                db.add_all([ev1, ev2, ev3])
                db.commit()

                # Run rescue verification
                await run_rescue_investigation(tx.id, user_id)

                return {
                    "scenario": 2,
                    "title": "Payment Succeeds on Server, Client Response Lost",
                    "transaction_id": tx.id,
                    "status": "SUCCESS",
                    "outcome": "Backend verified merchant settlement. Payment confirmed SUCCESS; no refund required."
                }

            elif s_id == "3":
                # SCENARIO 3: Main ₹4,000 debit reported, beneficiary unconfirmed
                tx = Transaction(
                    id=f"tx_scen3_{uuid.uuid4().hex[:8]}",
                    user_id=user_id,
                    merchant_id=merchant_id,
                    amount=amount,
                    currency="INR",
                    status="OUTCOME_UNKNOWN",
                    provider="UPI_SIMULATOR",
                    upi_ref_no=f"UPI-2026-{uuid.uuid4().hex[:8].upper()}",
                    error_code="E_BENEFICIARY_TIMEOUT",
                    failure_reason="Debit confirmed by bank; beneficiary confirmation timed out.",
                    payer_bank="HDFC Bank",
                    beneficiary_bank="ICICI Bank",
                    is_synthetic=True,
                    created_at=now
                )
                db.add(tx)
                db.flush()

                ev1 = PaymentEvent(
                    transaction_id=tx.id,
                    event_type="INITIATED",
                    source="UPI_CLIENT",
                    title="Payment Initiated (DEMO / SIMULATED)",
                    description=f"₹{amount:,.2f} initiated from mobile scanner.",
                    verification_status="VERIFIED",
                    is_synthetic=True,
                    event_timestamp=now
                )
                ev2 = PaymentEvent(
                    transaction_id=tx.id,
                    event_type="DEBIT_REPORTED",
                    source="SIMULATED_PAYER_BANK",
                    title="Payer Debited (DEMO / SIMULATED)",
                    description=f"HDFC Bank confirmed ₹{amount:,.2f} debited from customer account.",
                    verification_status="VERIFIED",
                    is_synthetic=True,
                    event_timestamp=now + timedelta(seconds=1)
                )
                ev3 = PaymentEvent(
                    transaction_id=tx.id,
                    event_type="BENEFICIARY_PENDING",
                    source="DEMO_MERCHANT",
                    title="Merchant Confirmation Missing (DEMO / SIMULATED)",
                    description="Merchant POS timed out awaiting credit signal from switch.",
                    verification_status="UNVERIFIED",
                    is_synthetic=True,
                    event_timestamp=now + timedelta(seconds=3)
                )
                db.add_all([ev1, ev2, ev3])
                db.commit()

                # Trigger LangGraph Rescue Agent
                res = await run_rescue_investigation(tx.id, user_id)

                return {
                    "scenario": 3,
                    "title": "Debit Reported, Beneficiary Confirmation Missing",
                    "transaction_id": tx.id,
                    "status": "OUTCOME_UNKNOWN",
                    "outcome": "Raah Rescue workflow invoked. Registered resolution case and scheduled follow-up.",
                    "agent_state": res.get("status_summary")
                }

            elif s_id == "4":
                # SCENARIO 4: Reversal has been initiated but completion is pending
                # Locate primary ₹4,000 transaction or create one
                target_tx = db.query(Transaction).filter(
                    Transaction.status == "OUTCOME_UNKNOWN"
                ).first()

                if not target_tx:
                    target_tx = Transaction(
                        id=f"tx_scen4_{uuid.uuid4().hex[:8]}",
                        user_id=user_id,
                        merchant_id=merchant_id,
                        amount=amount,
                        status="OUTCOME_UNKNOWN",
                        is_synthetic=True,
                        created_at=now - timedelta(minutes=20)
                    )
                    db.add(target_tx)
                    db.flush()

                ev_rev_init = PaymentEvent(
                    transaction_id=target_tx.id,
                    event_type="REVERSAL_INITIATED",
                    source="NPCI_UPI_GATEWAY",
                    provider_reference=f"NPCI-REV-BATCH-{uuid.uuid4().hex[:6].upper()}",
                    title="Reversal Initiated by Switch (DEMO / SIMULATED)",
                    description="Settlement reconciliation window closed without merchant credit. Switch transmitted automated reversal batch to payer bank.",
                    verification_status="VERIFIED",
                    is_synthetic=True,
                    event_timestamp=now
                )
                db.add(ev_rev_init)
                
                # Update case action log if case exists
                case = db.query(ResolutionCase).filter(ResolutionCase.transaction_id == target_tx.id).first()
                if case:
                    case.status = "RECOVERY_IN_PROGRESS"
                    case.latest_ai_action = "Switch initiated auto-reversal batch. Awaiting payer bank credit confirmation."
                    case.last_checked_at = now
                    log = CaseActionLog(
                        case_id=case.id,
                        agent_type="RAAH_RESCUE",
                        tool_invoked="poll_reversal_switch",
                        action_title="Switch Reversal Batch Detected",
                        action_description="NPCI switch registered automated reversal batch. Payer credit pending.",
                        input_payload=json.dumps({"transaction_id": target_tx.id}),
                        output_payload=json.dumps({"reversal_batch": ev_rev_init.provider_reference}),
                        validation_outcome="VALIDATED",
                        execution_outcome="SUCCESS"
                    )
                    db.add(log)

                db.commit()
                return {
                    "scenario": 4,
                    "title": "Reversal Initiated, Credit Pending",
                    "transaction_id": target_tx.id,
                    "outcome": "Reversal batch transmitted by payment switch. Timeline updated with in-transit state."
                }

            elif s_id == "5":
                # SCENARIO 5: Verified reversal completion event arrives
                target_tx = db.query(Transaction).filter(
                    Transaction.status == "OUTCOME_UNKNOWN"
                ).first()

                if not target_tx:
                    target_tx = db.query(Transaction).order_by(Transaction.created_at.desc()).first()

                target_tx.status = "REVERSED"
                target_tx.updated_at = now

                ev_rev_comp = PaymentEvent(
                    transaction_id=target_tx.id,
                    event_type="REVERSAL_COMPLETED",
                    source="SIMULATED_PAYER_BANK",
                    provider_reference=f"RRN-HDFC-CREDIT-{uuid.uuid4().hex[:6].upper()}",
                    title="Refund Credited to Payer Bank (DEMO / SIMULATED)",
                    description=f"HDFC Bank verified ₹{target_tx.amount:,.2f} credited back to customer account.",
                    verification_status="VERIFIED",
                    is_synthetic=True,
                    event_timestamp=now
                )
                db.add(ev_rev_comp)

                case = db.query(ResolutionCase).filter(ResolutionCase.transaction_id == target_tx.id).first()
                if case:
                    case.status = "RESOLVED"
                    case.latest_ai_action = "Reversal verified by payer bank. Transaction fully resolved."
                    case.resolution_summary = f"Refund of ₹{target_tx.amount:,.2f} confirmed credited by HDFC Bank."
                    case.last_checked_at = now

                    log = CaseActionLog(
                        case_id=case.id,
                        agent_type="RAAH_RESCUE",
                        tool_invoked="verify_bank_reversal",
                        action_title="Reversal Credit Verified",
                        action_description=f"Confirmed customer bank credit with RRN {ev_rev_comp.provider_reference}. Case successfully closed.",
                        input_payload=json.dumps({"transaction_id": target_tx.id}),
                        output_payload=json.dumps({"status": "RESOLVED", "rrn": ev_rev_comp.provider_reference}),
                        validation_outcome="VALIDATED",
                        execution_outcome="SUCCESS"
                    )
                    db.add(log)

                db.commit()
                return {
                    "scenario": 5,
                    "title": "Verified Reversal Completion Event Arrives",
                    "transaction_id": target_tx.id,
                    "status": "REVERSED",
                    "outcome": "Refund credit verified from payer bank. Money Journey and AI Resolution Journey updated to RESOLVED."
                }

            elif s_id == "6":
                # SCENARIO 6: Trigger burst of failures to demonstrate Raah Pulse
                burst_count = 8
                for i in range(burst_count):
                    tx = Transaction(
                        id=f"tx_pulse_burst_{i}_{uuid.uuid4().hex[:6]}",
                        user_id=user_id,
                        merchant_id=merchant_id,
                        amount=round(400.0 + (i * 120.0), 2),
                        status="OUTCOME_UNKNOWN",
                        payer_bank="HDFC Bank",
                        gateway="NPCI_UPI_SWITCH",
                        error_code="E_TIMEDOUT_GATEWAY",
                        failure_reason="Gateway 504 Timeout during bank processing.",
                        is_synthetic=True,
                        created_at=now - timedelta(minutes=5 - (i * 0.5))
                    )
                    db.add(tx)
                db.commit()

                # Run pulse agent
                pulse_res = await RaahPulseAgent.analyze_telemetry_and_correlate()
                return {
                    "scenario": 6,
                    "title": "Cluster Spike on HDFC (Raah Pulse)",
                    "injected_failures": burst_count,
                    "pulse_outcome": pulse_res
                }

            elif s_id == "7":
                # SCENARIO 7: Duplicate payment attempt (RetryGuard check)
                from app.services.retryguard_service import RetryGuardService
                check = RetryGuardService.check_duplicate_risk(
                    db=db,
                    user_id=user_id,
                    merchant_id=merchant_id,
                    amount=amount,
                    window_minutes=15
                )
                return {
                    "scenario": 7,
                    "title": "Customer Attempts Possible Duplicate Payment",
                    "duplicate_risk_detected": check["has_potential_duplicate"],
                    "warning_message": check["warning_message"],
                    "existing_transaction_id": check.get("existing_transaction_id")
                }

            elif s_id == "8":
                # SCENARIO 8: Case becomes overdue under RBI policy
                case = db.query(ResolutionCase).filter(
                    ResolutionCase.status.in_(["INVESTIGATING", "RECOVERY_IN_PROGRESS"])
                ).first()

                if case:
                    # Set regulatory deadline in the past
                    case.regulatory_deadline = now - timedelta(days=2)
                    case.status = "ESCALATED"
                    case.compensation_eligible = True
                    case.latest_ai_action = "Case exceeded regulatory resolution deadline. Escalated to operations for compensation verification."
                    
                    log = CaseActionLog(
                        case_id=case.id,
                        agent_type="RAAH_RESCUE",
                        tool_invoked="overdue_tat_check",
                        action_title="Regulatory Turnaround Time Exceeded",
                        action_description="RBI TAT deadline (T+5) elapsed without confirmed settlement or reversal. Escalated for statutory compensation verification.",
                        input_payload=json.dumps({"case_id": case.id}),
                        output_payload=json.dumps({"overdue_days": 2, "potential_compensation": 200.0}),
                        validation_outcome="VALIDATED",
                        execution_outcome="SUCCESS"
                    )
                    db.add(log)
                    db.commit()

                    return {
                        "scenario": 8,
                        "title": "Case Becomes Overdue Under RBI Policy",
                        "case_number": case.case_number,
                        "status": "ESCALATED",
                        "outcome": "Regulatory deadline passed. Potential statutory compensation marked for verification (₹100/day)."
                    }
                else:
                    return {"scenario": 8, "message": "No active recovery case to simulate overdue TAT on."}

            return {"error": f"Unknown scenario {scenario_id}"}
        finally:
            db.close()
