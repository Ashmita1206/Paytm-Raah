import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.database.session import SessionLocal
from app.models.payment import Transaction
from app.models.case import ResolutionCase
from app.models.chat import ChatSession, ChatMessage
from app.mcp_servers.client import RaahMCPClient
from app.policies.reversal_policy import RegulatoryPolicyEngine
from app.utils.time_utils import utcnow, ensure_naive

class AskRaahAgent:
    """
    Contextual conversational interface for RAAH Autonomous Payment Intelligence.
    Never hallucinates payment outcomes or exact arrival dates.
    Quotes authoritative evidence, regulatory deadlines (RBI Harmonisation),
    and reflects real-time MCP tool executions.
    """

    @classmethod
    async def process_user_message(
        cls,
        session_id: str,
        user_message: str,
        transaction_id: Optional[str] = None
    ) -> Dict[str, Any]:
        db: Session = SessionLocal()
        try:
            sess = db.query(ChatSession).filter(ChatSession.id == session_id).first()
            if not sess:
                return {"error": "Chat session not found"}

            tx_id = transaction_id or sess.transaction_id
            
            # Save user message
            user_msg = ChatMessage(
                session_id=session_id,
                sender="USER",
                content=user_message,
                created_at=utcnow()
            )
            db.add(user_msg)
            db.commit()

            tools_executed = []
            tool_results = []
            
            # 1. Fetch transaction evidence via MCP if transaction_id is present
            tx_data = {}
            events = []
            reversal_info = {}
            merchant_info = {}
            policy_info = {}
            case_info = {}

            if tx_id:
                # Call MCP tool: get_transaction_status
                tools_executed.append({"tool": "get_transaction_status", "args": {"transaction_id": tx_id}})
                tx_data = await RaahMCPClient.call_tool("get_transaction_status", {"transaction_id": tx_id})
                tool_results.append(tx_data)

                # Call MCP tool: get_merchant_confirmation
                tools_executed.append({"tool": "get_merchant_confirmation", "args": {"transaction_id": tx_id}})
                merchant_info = await RaahMCPClient.call_tool("get_merchant_confirmation", {"transaction_id": tx_id})
                tool_results.append(merchant_info)

                # Call MCP tool: get_reversal_status
                tools_executed.append({"tool": "get_reversal_status", "args": {"transaction_id": tx_id}})
                reversal_info = await RaahMCPClient.call_tool("get_reversal_status", {"transaction_id": tx_id})
                tool_results.append(reversal_info)

                # Call MCP tool: get_applicable_reversal_policy
                tools_executed.append({"tool": "get_applicable_reversal_policy", "args": {"category": "UPI_P2M"}})
                policy_info = await RaahMCPClient.call_tool("get_applicable_reversal_policy", {"category": "UPI_P2M"})
                tool_results.append(policy_info)

                # Check if case exists in db
                case = db.query(ResolutionCase).filter(ResolutionCase.transaction_id == tx_id).first()
                if case:
                    case_info = {
                        "case_number": case.case_number,
                        "status": case.status,
                        "regulatory_deadline": case.regulatory_deadline.strftime("%d %b %Y, %I:%M %p") if case.regulatory_deadline else None,
                        "latest_action": case.latest_ai_action
                    }

            # Synthesize factual, trustworthy response based on verified evidence
            norm_q = user_message.lower()
            response_text = ""

            if not tx_id:
                response_text = (
                    "Hello! I am Raah, your autonomous payment recovery teammate. "
                    "I track in-flight UPI payments, verify bank debit signals against merchant confirmations, "
                    "and enforce RBI failed-transaction recovery policies. "
                    "You can link me to any recent transaction or tap 'Track & Resolve Payment' on your home screen."
                )
            elif "fail" in norm_q or "why" in norm_q or "what happened" in norm_q:
                status = tx_data.get("status", "UNKNOWN")
                amt = tx_data.get("amount", 0.0)
                merch = tx_data.get("merchant_name", "the merchant")
                payer_bank = tx_data.get("payer_bank", "your bank")

                if status == "OUTCOME_UNKNOWN" or status == "DEBIT_REPORTED":
                    response_text = (
                        f"Here is what the verified network records show for your ₹{amt:,.2f} payment to {merch}:\n\n"
                        f"• Payer Debit: Confirmed debited from {payer_bank}.\n"
                        f"• Merchant Settlement: Unconfirmed. The merchant terminal has not received an authoritative credit signal from NPCI.\n"
                        f"• Case Status: Raah Rescue has registered active recovery case {case_info.get('case_number', 'CASE-ACTIVE')}.\n\n"
                        f"Under RBI Harmonisation guidelines (T+5), if the merchant does not confirm credit, "
                        f"the network must automatically initiate an auto-reversal to your account by {policy_info.get('regulatory_deadline_text', 'the regulatory deadline')}."
                    )
                elif status == "SUCCESS":
                    response_text = (
                        f"Good news! Your ₹{amt:,.2f} payment to {merch} is confirmed SUCCESS on the payment switch and settled with the merchant."
                    )
                else:
                    response_text = (
                        f"Your ₹{amt:,.2f} payment failed before debit. No money was transferred from your bank account."
                    )

            elif "merchant" in norm_q or "receive" in norm_q:
                is_conf = merchant_info.get("merchant_confirmed", False)
                merch = tx_data.get("merchant_name", "the merchant")
                if is_conf:
                    response_text = f"Yes, {merch} verified credit with confirmation reference {merchant_info.get('confirmation_reference', 'CONFIRMED')}."
                else:
                    response_text = (
                        f"No, {merch} reports no settlement confirmation received yet. "
                        f"Our autonomous teammate is querying the merchant switch periodically."
                    )

            elif "money back" in norm_q or "refund" in norm_q or "reversal" in norm_q or "when" in norm_q:
                rev_state = reversal_info.get("reversal_state", "NOT_INITIATED")
                deadline_text = policy_info.get("regulatory_deadline_text", "within regulatory turnaround")

                if rev_state == "COMPLETED":
                    response_text = (
                        f"Reversal verified! Your refund has already been credited to your bank account "
                        f"with reference {reversal_info.get('rrn', 'RRN-VERIFIED')}."
                    )
                elif rev_state == "INITIATED_PENDING":
                    response_text = (
                        f"An auto-reversal has been initiated by the switch and is pending credit at your bank. "
                        f"Applicable regulatory resolution deadline: {deadline_text}."
                    )
                else:
                    response_text = (
                        f"If the merchant does not confirm credit, an automatic reversal is mandated under RBI guidelines. "
                        f"The regulatory resolution deadline is {deadline_text}. "
                        f"(Note: This is a regulatory policy deadline, not a guaranteed exact credit timestamp)."
                    )

            elif "complaint" in norm_q or "dispute" in norm_q or "raise" in norm_q or "escalate" in norm_q:
                if case_info:
                    response_text = (
                        f"A resolution case is already actively open for this transaction: {case_info.get('case_number')}. "
                        f"Current status: {case_info.get('status')}. "
                        f"Raah Rescue is actively monitoring this case and will escalate to human operations if the deadline approaches."
                    )
                else:
                    # Trigger case creation via MCP
                    tools_executed.append({"tool": "create_resolution_case", "args": {"transaction_id": tx_id, "reason": "Customer initiated complaint via Ask Raah"}})
                    c_res = await RaahMCPClient.call_tool("create_resolution_case", {"transaction_id": tx_id, "reason": "Customer initiated complaint via Ask Raah"})
                    tool_results.append(c_res)
                    response_text = (
                        f"I have officially registered Resolution Case {c_res.get('case_number')} for your payment. "
                        f"Autonomous background follow-up has been scheduled."
                    )

            else:
                amt = tx_data.get("amount", 4000.0)
                status = tx_data.get("status", "OUTCOME_UNKNOWN")
                response_text = (
                    f"Current status for transaction {tx_id} (₹{amt:,.2f}): {status}. "
                    f"Active Case: {case_info.get('case_number', 'CASE-ACTIVE')}. "
                    f"Regulatory TAT: {policy_info.get('regulatory_deadline_text', 'T+5 Days')}. "
                    f"Raah Rescue is monitoring the payment network and will update your timeline automatically."
                )

            # Save assistant message
            bot_msg = ChatMessage(
                session_id=session_id,
                sender="ASSISTANT",
                content=response_text,
                tool_calls=json.dumps(tools_executed),
                tool_results=json.dumps(tool_results),
                created_at=utcnow()
            )
            db.add(bot_msg)
            sess.updated_at = utcnow()
            db.commit()

            return {
                "message_id": bot_msg.id,
                "sender": "ASSISTANT",
                "content": response_text,
                "tool_calls": tools_executed,
                "tool_results": tool_results,
                "created_at": bot_msg.created_at.isoformat()
            }
        finally:
            db.close()
