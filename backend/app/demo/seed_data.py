import json
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.database.session import SessionLocal, Base, engine
from app.models.user import User, DemoMerchant
from app.models.payment import Transaction, PaymentEvent, ProviderObservation
from app.models.case import ResolutionCase, CaseActionLog, ScheduledFollowup
from app.models.incident import IncidentRecord, IncidentTransactionLink
from app.models.chat import ChatSession, ChatMessage
from app.models.notification import Notification
from app.policies.reversal_policy import RegulatoryPolicyEngine
from app.utils.time_utils import utcnow, ensure_naive

def reset_database():
    """Drops and recreates all tables."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

def seed_standard_data():
    """Seeds the initial users, demo merchants, Transaction A/B/C/D, and Incident cluster."""
    db: Session = SessionLocal()
    try:
        now = utcnow()

        # 1. Primary Demo User
        user = User(
            id="user_default_01",
            phone="+919876543210",
            name="Rahul Sharma",
            upi_vpa="rahul.sharma@paytm",
            created_at=now - timedelta(days=30)
        )
        db.add(user)

        # 2. Demo Merchants
        merchants = [
            DemoMerchant(
                id="merch_grocery_01",
                merchant_name="Demo Fresh Grocery Store",
                upi_vpa="grocery@paytm",
                category="GROCERY",
                verified=True,
                active=True,
                logo_symbol="🛒",
                default_amount=4000.0,
                created_at=now - timedelta(days=60)
            ),
            DemoMerchant(
                id="merch_cafe_02",
                merchant_name="Demo Artisanal Cafe",
                upi_vpa="cafe@paytm",
                category="DINING",
                verified=True,
                active=True,
                logo_symbol="☕",
                default_amount=750.0,
                created_at=now - timedelta(days=45)
            ),
            DemoMerchant(
                id="merch_pharmacy_03",
                merchant_name="Demo City Medico Pharmacy",
                upi_vpa="pharmacy@paytm",
                category="HEALTHCARE",
                verified=True,
                active=True,
                logo_symbol="💊",
                default_amount=1200.0,
                created_at=now - timedelta(days=30)
            ),
            DemoMerchant(
                id="merch_electronics_04",
                merchant_name="Demo Digital Tech Hub",
                upi_vpa="techhub@paytm",
                category="ELECTRONICS",
                verified=True,
                active=True,
                logo_symbol="💻",
                default_amount=15500.0,
                created_at=now - timedelta(days=20)
            )
        ]
        for m in merchants:
            db.add(m)
        db.flush()

        # 3. TRANSACTION A (FLAGSHIP CASE): ₹4,000 Grocery, Debit reported, Beneficiary confirmation missing
        tx_a_id = "tx_demo_4000_grocery"
        tx_a = Transaction(
            id=tx_a_id,
            user_id=user.id,
            merchant_id="merch_grocery_01",
            amount=4000.0,
            currency="INR",
            status="OUTCOME_UNKNOWN",
            provider="UPI_SIMULATOR",
            upi_ref_no="UPI-2026-98741029",
            idempotency_key="idemp_grocery_4000_01",
            payer_bank="HDFC Bank",
            beneficiary_bank="ICICI Bank",
            gateway="NPCI_UPI_SWITCH",
            error_code="E_BENEFICIARY_TIMEOUT",
            failure_reason="Debit acknowledged by payer bank; beneficiary confirmation timed out at NPCI switch.",
            is_synthetic=True,
            created_at=now - timedelta(minutes=14)
        )
        db.add(tx_a)
        db.flush()

        # Timeline A (Money Journey) for Transaction A
        events_a = [
            PaymentEvent(
                id="ev_a_01",
                transaction_id=tx_a.id,
                event_type="INITIATED",
                source="UPI_CLIENT",
                provider_reference="REQ-UPI-8841",
                title="Payment Initiated",
                description="Smart QR scanned. Payment instruction of ₹4,000 transmitted to NPCI switch.",
                verification_status="VERIFIED",
                is_synthetic=True,
                event_timestamp=now - timedelta(minutes=14)
            ),
            PaymentEvent(
                id="ev_a_02",
                transaction_id=tx_a.id,
                event_type="DEBIT_REPORTED",
                source="SIMULATED_PAYER_BANK",
                provider_reference="HDFC-DEBIT-77491",
                title="Payer Account Debited",
                description="HDFC Bank reports ₹4,000 successfully debited from customer account ending in 4102.",
                verification_status="VERIFIED",
                is_synthetic=True,
                event_timestamp=now - timedelta(minutes=13, seconds=50)
            ),
            PaymentEvent(
                id="ev_a_03",
                transaction_id=tx_a.id,
                event_type="GATEWAY_PROCESSING",
                source="NPCI_UPI_GATEWAY",
                provider_reference="NPCI-RRN-9921",
                title="Switch Processing",
                description="Transaction routed to ICICI Bank (Beneficiary). Settlement acknowledgement pending.",
                verification_status="VERIFIED",
                is_synthetic=True,
                event_timestamp=now - timedelta(minutes=13, seconds=35)
            ),
            PaymentEvent(
                id="ev_a_04",
                transaction_id=tx_a.id,
                event_type="BENEFICIARY_PENDING",
                source="DEMO_MERCHANT",
                provider_reference="MERCH-POLL-TIMEOUT",
                title="Beneficiary Confirmation Missing",
                description="Merchant terminal timed out while waiting for credit push notification from switch.",
                verification_status="UNVERIFIED",
                is_synthetic=True,
                event_timestamp=now - timedelta(minutes=13, seconds=20)
            )
        ]
        for ev in events_a:
            db.add(ev)

        # Active Resolution Case for Transaction A
        policy_eval = RegulatoryPolicyEngine.evaluate_transaction("UPI_P2M", tx_a.created_at)
        case_a = ResolutionCase(
            id="case_grocery_4000",
            case_number="CASE-2026-8941",
            transaction_id=tx_a.id,
            user_id=user.id,
            status="INVESTIGATING",
            category="UPI_P2M_DEBIT_WITHOUT_CONFIRMATION",
            policy_name=policy_eval["policy_name"],
            regulatory_deadline=policy_eval["regulatory_deadline"],
            policy_explanation=policy_eval["disclaimer"],
            assigned_agent="RAAH_RESCUE",
            latest_ai_action="Autonomous status check scheduled. Payer debited; merchant confirmation unverified.",
            last_checked_at=now - timedelta(minutes=4),
            next_check_at=now + timedelta(minutes=6),
            retry_count=1
        )
        db.add(case_a)
        db.flush()

        # Timeline B (AI Resolution Journey) for Transaction A
        actions_a = [
            CaseActionLog(
                id="act_a_01",
                case_id=case_a.id,
                agent_type="RAAH_RESCUE",
                tool_invoked="investigation_started",
                action_title="Investigation Initiated",
                action_description="Raah Rescue detected uncertain payment outcome following client timeout.",
                input_payload=json.dumps({"transaction_id": tx_a.id, "amount": 4000.0}),
                output_payload=json.dumps({"trigger": "UNRESOLVED_PAYMENT"}),
                validation_outcome="VALIDATED",
                execution_outcome="SUCCESS",
                created_at=now - timedelta(minutes=13)
            ),
            CaseActionLog(
                id="act_a_02",
                case_id=case_a.id,
                agent_type="RAAH_RESCUE",
                tool_invoked="get_transaction_status",
                action_title="Payment Status Retrieved via MCP",
                action_description="Authoritative status retrieved from HDFC Bank and NPCI switch.",
                input_payload=json.dumps({"transaction_id": tx_a.id}),
                output_payload=json.dumps({"status": "OUTCOME_UNKNOWN", "payer_debited": True}),
                validation_outcome="VALIDATED",
                execution_outcome="SUCCESS",
                created_at=now - timedelta(minutes=12, seconds=45)
            ),
            CaseActionLog(
                id="act_a_03",
                case_id=case_a.id,
                agent_type="RAAH_RESCUE",
                tool_invoked="get_merchant_confirmation",
                action_title="Merchant Record Checked via MCP",
                action_description="Queried Demo Fresh Grocery Store POS gateway. No settlement push recorded.",
                input_payload=json.dumps({"merchant_id": "merch_grocery_01"}),
                output_payload=json.dumps({"confirmed": False, "terminal_status": "TIMEOUT"}),
                validation_outcome="VALIDATED",
                execution_outcome="SUCCESS",
                created_at=now - timedelta(minutes=12, seconds=30)
            ),
            CaseActionLog(
                id="act_a_04",
                case_id=case_a.id,
                agent_type="RAAH_RESCUE",
                tool_invoked="get_applicable_reversal_policy",
                action_title="Regulatory Policy Evaluated",
                action_description="Evaluated RBI Harmonisation TAT Circular (UPI P2M). Regulatory deadline set to T+5 days.",
                input_payload=json.dumps({"category": "UPI_P2M"}),
                output_payload=json.dumps({"tat_working_days": 5, "auto_reversal_mandated": True}),
                validation_outcome="VALIDATED",
                execution_outcome="SUCCESS",
                created_at=now - timedelta(minutes=12, seconds=15)
            ),
            CaseActionLog(
                id="act_a_05",
                case_id=case_a.id,
                agent_type="RAAH_RESCUE",
                tool_invoked="schedule_case_followup",
                action_title="Autonomous Follow-up Scheduled",
                action_description="Background recheck scheduled with exponential backoff. Polling switch for reversal/settlement.",
                input_payload=json.dumps({"case_id": case_a.id, "delay_seconds": 600}),
                output_payload=json.dumps({"scheduled_time": (now + timedelta(minutes=6)).isoformat()}),
                validation_outcome="VALIDATED",
                execution_outcome="SUCCESS",
                created_at=now - timedelta(minutes=4)
            )
        ]
        for act in actions_a:
            db.add(act)

        # 4. TRANSACTION B: ₹750 Demo Cafe (Success on provider, frontend dropped)
        tx_b = Transaction(
            id="tx_demo_750_cafe",
            user_id=user.id,
            merchant_id="merch_cafe_02",
            amount=750.0,
            currency="INR",
            status="SUCCESS",
            provider="UPI_SIMULATOR",
            upi_ref_no="UPI-2026-11209384",
            idempotency_key="idemp_cafe_750_01",
            payer_bank="ICICI Bank",
            beneficiary_bank="State Bank of India",
            gateway="NPCI_UPI_SWITCH",
            client_response_dropped=True,
            is_synthetic=True,
            created_at=now - timedelta(hours=2)
        )
        db.add(tx_b)
        db.flush()

        events_b = [
            PaymentEvent(
                id="ev_b_01",
                transaction_id=tx_b.id,
                event_type="INITIATED",
                source="UPI_CLIENT",
                title="Payment Initiated",
                description="QR scanned for ₹750 at Demo Artisanal Cafe.",
                verification_status="VERIFIED",
                is_synthetic=True,
                event_timestamp=now - timedelta(hours=2)
            ),
            PaymentEvent(
                id="ev_b_02",
                transaction_id=tx_b.id,
                event_type="DEBIT_REPORTED",
                source="SIMULATED_PAYER_BANK",
                title="Payer Debited",
                description="ICICI Bank debited ₹750.",
                verification_status="VERIFIED",
                is_synthetic=True,
                event_timestamp=now - timedelta(hours=2, seconds=-5)
            ),
            PaymentEvent(
                id="ev_b_03",
                transaction_id=tx_b.id,
                event_type="BENEFICIARY_CONFIRMED",
                source="DEMO_MERCHANT",
                title="Merchant Confirmed Credit",
                description="Cafe POS confirmed order #CAFE-901 paid and fulfilled. Backend verified.",
                verification_status="VERIFIED",
                is_synthetic=True,
                event_timestamp=now - timedelta(hours=2, seconds=-12)
            )
        ]
        for ev in events_b:
            db.add(ev)

        # 5. TRANSACTION C: ₹1,200 Demo Pharmacy (Failed before debit)
        tx_c = Transaction(
            id="tx_demo_1200_pharmacy",
            user_id=user.id,
            merchant_id="merch_pharmacy_03",
            amount=1200.0,
            currency="INR",
            status="FAILED",
            provider="UPI_SIMULATOR",
            upi_ref_no="UPI-2026-33910291",
            idempotency_key="idemp_pharmacy_1200_01",
            payer_bank="HDFC Bank",
            beneficiary_bank="Axis Bank",
            gateway="NPCI_UPI_SWITCH",
            error_code="E_INSUFFICIENT_FUNDS_OR_EXPIRED",
            failure_reason="Authentication failed prior to debit. No funds transferred.",
            is_synthetic=True,
            created_at=now - timedelta(days=1)
        )
        db.add(tx_c)
        db.flush()

        events_c = [
            PaymentEvent(
                id="ev_c_01",
                transaction_id=tx_c.id,
                event_type="INITIATED",
                source="UPI_CLIENT",
                title="Payment Initiated",
                description="₹1,200 initiated at Demo City Medico Pharmacy.",
                verification_status="VERIFIED",
                is_synthetic=True,
                event_timestamp=now - timedelta(days=1)
            ),
            PaymentEvent(
                id="ev_c_02",
                transaction_id=tx_c.id,
                event_type="PAYMENT_FAILED",
                source="SIMULATED_PAYER_BANK",
                title="Rejected Prior to Debit",
                description="HDFC Bank rejected request prior to debit: Session expired or invalid PIN.",
                verification_status="VERIFIED",
                is_synthetic=True,
                event_timestamp=now - timedelta(days=1, seconds=-3)
            )
        ]
        for ev in events_c:
            db.add(ev)

        # 6. PULSE INCIDENT CLUSTER: 12 synthetic transactions sharing gateway timeout pattern on HDFC
        inc_id = "inc_demo_hdfc_spike"
        incident = IncidentRecord(
            id=inc_id,
            incident_number="INC-2026-042",
            title="HDFC UPI Switch - 504 Gateway Timeout Spike",
            error_category="E_TIMEDOUT_GATEWAY",
            provider="NPCI_UPI_SWITCH",
            bank="HDFC Bank",
            affected_count=12,
            baseline_failure_rate=1.2,
            observed_failure_rate=31.6,
            status="CORRELATED",
            summary=(
                "Raah Pulse detected an abnormal concentration of 12 timed-out transactions on HDFC Bank "
                "via NPCI switch within the last 25 minutes. Observed failure rate spiked to 31.6% vs 1.2% baseline. "
                "Transactions exhibit payer debit acknowledgement with downstream beneficiary response timeout."
            ),
            recommended_mitigation=(
                "1. Implement dynamic switch traffic diversion for HDFC payer VPAs. "
                "2. Activate RetryGuard in mobile client to warn users against immediate re-attempts. "
                "3. Coordinate with HDFC UPI operations desk."
            ),
            ai_actions_taken=json.dumps([
                f"[{(now - timedelta(minutes=22)).strftime('%H:%M:%S')}] Pulse anomaly detector flagged cluster of 12 transactions.",
                f"[{(now - timedelta(minutes=20)).strftime('%H:%M:%S')}] Correlated individual customer recovery cases including CASE-2026-8941.",
                f"[{(now - timedelta(minutes=18)).strftime('%H:%M:%S')}] Dynamic routing advisory broadcasted to Paytm payment switch."
            ]),
            detected_at=now - timedelta(minutes=25)
        )
        db.add(incident)
        db.flush()

        # Link Transaction A to this incident
        case_a.correlated_incident_id = incident.id
        link_a = IncidentTransactionLink(
            id="link_a_01",
            incident_id=incident.id,
            transaction_id=tx_a.id,
            case_id=case_a.id,
            correlation_confidence=0.99
        )
        db.add(link_a)

        # Create 11 additional synthetic cluster transactions
        for i in range(1, 12):
            cluster_tx = Transaction(
                id=f"tx_cluster_hdfc_{i:02d}",
                user_id=user.id,
                merchant_id="merch_grocery_01" if i % 2 == 0 else "merch_cafe_02",
                amount=round(500.0 + (i * 275.50), 2),
                currency="INR",
                status="OUTCOME_UNKNOWN",
                provider="UPI_SIMULATOR",
                upi_ref_no=f"UPI-2026-CLUS-{i:04d}",
                payer_bank="HDFC Bank",
                beneficiary_bank="State Bank of India",
                gateway="NPCI_UPI_SWITCH",
                error_code="E_TIMEDOUT_GATEWAY",
                failure_reason="Gateway 504 Timeout during beneficiary routing.",
                is_synthetic=True,
                created_at=now - timedelta(minutes=24 - (i * 1.5))
            )
            db.add(cluster_tx)
            db.flush()

            # Create link
            db.add(IncidentTransactionLink(
                id=f"link_cluster_{i:02d}",
                incident_id=incident.id,
                transaction_id=cluster_tx.id,
                correlation_confidence=0.96
            ))

        # 7. Initial Contextual Chat Session
        chat_sess = ChatSession(
            id="sess_demo_grocery_01",
            user_id=user.id,
            transaction_id=tx_a.id,
            case_id=case_a.id,
            title="Inquiry: ₹4,000 to Fresh Grocery Store",
            created_at=now - timedelta(minutes=10)
        )
        db.add(chat_sess)
        db.flush()

        msgs = [
            ChatMessage(
                id="msg_demo_01",
                session_id=chat_sess.id,
                sender="USER",
                content="Why did my ₹4,000 payment fail? Did the grocery store get my money?",
                created_at=now - timedelta(minutes=10)
            ),
            ChatMessage(
                id="msg_demo_02",
                session_id=chat_sess.id,
                sender="ASSISTANT",
                content=(
                    "Here is what the verified network records show for your ₹4,000.00 payment to Demo Fresh Grocery Store:\n\n"
                    "• Payer Debit: Confirmed debited from HDFC Bank.\n"
                    "• Merchant Settlement: Unconfirmed. The grocery store terminal has not received an authoritative credit push from NPCI switch.\n"
                    "• Active Case: Raah Rescue has registered Case CASE-2026-8941.\n\n"
                    "Under RBI Harmonisation guidelines (T+5), if the merchant does not confirm credit, "
                    f"the network must initiate an auto-reversal to your account by {policy_eval['regulatory_deadline_text']}."
                ),
                tool_calls=json.dumps([
                    {"tool": "get_transaction_status", "args": {"transaction_id": tx_a.id}},
                    {"tool": "get_merchant_confirmation", "args": {"transaction_id": tx_a.id}},
                    {"tool": "get_applicable_reversal_policy", "args": {"category": "UPI_P2M"}}
                ]),
                tool_results=json.dumps([
                    {"status": "OUTCOME_UNKNOWN", "amount": 4000.0},
                    {"merchant_confirmed": False},
                    {"policy": policy_eval["policy_name"]}
                ]),
                created_at=now - timedelta(minutes=9, seconds=50)
            )
        ]
        for m in msgs:
            db.add(m)

        # 8. Initial in-app Notification
        notif = Notification(
            id="notif_demo_01",
            user_id=user.id,
            title="Raah Rescue Active: ₹4,000 Payment",
            message="We detected an unconfirmed outcome for your Grocery payment. Recovery Case CASE-2026-8941 is actively investigating.",
            type="CASE_UPDATE",
            read=False,
            created_at=now - timedelta(minutes=12)
        )
        db.add(notif)

        db.commit()
        return {
            "status": "SUCCESS",
            "message": "Database seeded with realistic fintech demo data",
            "primary_transaction_id": tx_a.id,
            "case_number": case_a.case_number,
            "incident_number": incident.incident_number
        }
    finally:
        db.close()
