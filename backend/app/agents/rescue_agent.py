import json
import logging
from typing import Dict, Any, List, Optional, TypedDict
from datetime import datetime, timezone
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from app.mcp_servers.client import RaahMCPClient
from app.utils.time_utils import utcnow, ensure_naive

logger = logging.getLogger("raah.rescue_agent")

class RescueAgentState(TypedDict):
    transaction_id: str
    user_id: Optional[str]
    transaction_data: Dict[str, Any]
    payment_events: List[Dict[str, Any]]
    merchant_confirmation: Dict[str, Any]
    reversal_status: Dict[str, Any]
    evidence_classification: str
    applicable_policy: Dict[str, Any]
    case_data: Dict[str, Any]
    next_action: str
    action_result: Dict[str, Any]
    execution_history: List[str]
    is_terminal: bool
    status_summary: str


# Node 1: Load Transaction Details via MCP
async def load_transaction(state: RescueAgentState) -> Dict[str, Any]:
    tx_id = state["transaction_id"]
    res = await RaahMCPClient.call_tool("get_transaction_status", {"transaction_id": tx_id})
    history = state.get("execution_history", []) + ["load_transaction"]
    return {
        "transaction_data": res,
        "execution_history": history
    }


# Node 2: Retrieve Chronological Payment Events via MCP
async def retrieve_evidence(state: RescueAgentState) -> Dict[str, Any]:
    tx_id = state["transaction_id"]
    res = await RaahMCPClient.call_tool("get_payment_events", {"transaction_id": tx_id})
    events = res.get("events", []) if isinstance(res, dict) else []
    history = state.get("execution_history", []) + ["retrieve_evidence"]
    return {
        "payment_events": events,
        "execution_history": history
    }


# Node 3: Query Merchant Backend and Reversal Switch via MCP
async def check_merchant_and_reversal(state: RescueAgentState) -> Dict[str, Any]:
    tx_id = state["transaction_id"]
    merch_res = await RaahMCPClient.call_tool("get_merchant_confirmation", {"transaction_id": tx_id})
    rev_res = await RaahMCPClient.call_tool("get_reversal_status", {"transaction_id": tx_id})
    history = state.get("execution_history", []) + ["check_merchant_and_reversal"]
    return {
        "merchant_confirmation": merch_res,
        "reversal_status": rev_res,
        "execution_history": history
    }


# Node 4: Classify Evidence with strict deterministic logic
async def classify_evidence(state: RescueAgentState) -> Dict[str, Any]:
    tx_data = state.get("transaction_data", {})
    events = state.get("payment_events", [])
    merch = state.get("merchant_confirmation", {})
    rev = state.get("reversal_status", {})

    status = tx_data.get("status", "UNKNOWN")
    has_debit = any(e.get("event_type") == "DEBIT_REPORTED" for e in events)
    merchant_confirmed = merch.get("merchant_confirmed", False)
    reversal_state = rev.get("reversal_state", "NOT_INITIATED")

    # Classification categories
    if reversal_state == "COMPLETED":
        classification = "REVERSAL_COMPLETED"
    elif reversal_state == "INITIATED_PENDING":
        classification = "REVERSAL_IN_PROGRESS"
    elif status == "SUCCESS" and merchant_confirmed:
        classification = "VERIFIED_SUCCESS"
    elif status == "FAILED" and not has_debit:
        classification = "FAILED_PRE_DEBIT"
    elif has_debit and not merchant_confirmed:
        classification = "DEBITED_MERCHANT_UNCONFIRMED"
    elif status == "OUTCOME_UNKNOWN":
        classification = "OUTCOME_UNCERTAIN"
    else:
        classification = "INVESTIGATION_REQUIRED"

    history = state.get("execution_history", []) + [f"classify_evidence:{classification}"]
    return {
        "evidence_classification": classification,
        "execution_history": history
    }


# Node 5: Evaluate RBI Harmonisation Policy via MCP
async def evaluate_policy(state: RescueAgentState) -> Dict[str, Any]:
    classification = state.get("evidence_classification", "DEBITED_MERCHANT_UNCONFIRMED")
    category = "UPI_P2M"
    if classification == "FAILED_PRE_DEBIT":
        category = "PRE_DEBIT_FAILURE"

    policy_res = await RaahMCPClient.call_tool("get_applicable_reversal_policy", {"category": category})
    history = state.get("execution_history", []) + ["evaluate_policy"]
    return {
        "applicable_policy": policy_res,
        "execution_history": history
    }


# Node 6: Determine Permitted Next Action
async def determine_next_action(state: RescueAgentState) -> Dict[str, Any]:
    classification = state.get("evidence_classification", "")
    policy = state.get("applicable_policy", {})

    if classification == "VERIFIED_SUCCESS":
        action = "CLOSE_CASE_SUCCESS"
    elif classification == "REVERSAL_COMPLETED":
        action = "CLOSE_CASE_REVERSED"
    elif classification == "FAILED_PRE_DEBIT":
        action = "INFORM_PRE_DEBIT_REJECT"
    elif classification in ("DEBITED_MERCHANT_UNCONFIRMED", "OUTCOME_UNCERTAIN", "REVERSAL_IN_PROGRESS"):
        # Check if overdue
        if policy.get("is_overdue", False):
            action = "ESCALATE_OVERDUE_CASE"
        else:
            action = "ENSURE_CASE_AND_SCHEDULE_FOLLOWUP"
    else:
        action = "ENSURE_CASE_AND_SCHEDULE_FOLLOWUP"

    history = state.get("execution_history", []) + [f"determine_next_action:{action}"]
    return {
        "next_action": action,
        "execution_history": history
    }


# Node 7: Execute Authorized MCP Tool
async def execute_action(state: RescueAgentState) -> Dict[str, Any]:
    action = state.get("next_action", "")
    tx_id = state["transaction_id"]
    user_id = state.get("user_id", "user_default_01")
    classification = state.get("evidence_classification", "")
    policy = state.get("applicable_policy", {})

    action_result = {}
    is_terminal = False
    summary = ""

    if action == "ENSURE_CASE_AND_SCHEDULE_FOLLOWUP":
        # Create case idempotently
        case_res = await RaahMCPClient.call_tool("create_resolution_case", {
            "transaction_id": tx_id,
            "reason": f"Autonomous payment investigation active. Evidence shows {classification}. Payer debit reported; beneficiary confirmation missing."
        })
        case_id = case_res.get("case_id")
        
        # Schedule follow-up in 10 minutes (or demo simulated follow-up)
        followup_res = await RaahMCPClient.call_tool("schedule_case_followup", {
            "case_id": case_id,
            "delay_seconds": 60,
            "action_type": "RECHECK_PAYMENT_AND_MERCHANT_CONFIRMATION"
        })
        
        action_result = {"case": case_res, "followup": followup_res}
        summary = f"Case {case_res.get('case_number')} active under {policy.get('policy_name')}. Autonomous background verification scheduled."

    elif action == "ESCALATE_OVERDUE_CASE":
        case_res = await RaahMCPClient.call_tool("create_resolution_case", {
            "transaction_id": tx_id,
            "reason": f"Case exceeded RBI TAT of {policy.get('tat_working_days')} days. Escalated to operations."
        })
        case_id = case_res.get("case_id")
        esc_res = await RaahMCPClient.call_tool("request_human_review", {
            "case_id": case_id,
            "reason": f"Regulatory TAT ({policy.get('tat_hours')} hours) elapsed without credit confirmation. Potential compensation applicable."
        })
        action_result = {"case": case_res, "escalation": esc_res}
        summary = "Case escalated to Human Operations due to regulatory turnaround expiry."

    elif action == "CLOSE_CASE_SUCCESS":
        case_res = await RaahMCPClient.call_tool("create_resolution_case", {
            "transaction_id": tx_id,
            "reason": "Merchant confirmed credit. Payment verified successful."
        })
        case_id = case_res.get("case_id")
        upd = await RaahMCPClient.call_tool("update_resolution_case", {
            "case_id": case_id,
            "new_status": "RESOLVED",
            "notes": "Verified merchant confirmation received. Transaction settled."
        })
        action_result = {"case": case_res, "update": upd}
        is_terminal = True
        summary = "Payment confirmed successful by merchant. Case resolved."

    elif action == "CLOSE_CASE_REVERSED":
        case_res = await RaahMCPClient.call_tool("create_resolution_case", {
            "transaction_id": tx_id,
            "reason": "Reversal completion verified from payer bank."
        })
        case_id = case_res.get("case_id")
        upd = await RaahMCPClient.call_tool("update_resolution_case", {
            "case_id": case_id,
            "new_status": "RESOLVED",
            "notes": "Reversal credited to payer account. Transaction refunded."
        })
        action_result = {"case": case_res, "update": upd}
        is_terminal = True
        summary = "Reversal credited to bank account. Case resolved."

    else:
        action_result = {"info": "Pre-debit reject; no funds debited."}
        is_terminal = True
        summary = "Payment failed prior to debit. No funds transferred."

    history = state.get("execution_history", []) + [f"execute_action:{action}"]
    return {
        "action_result": action_result,
        "is_terminal": is_terminal,
        "status_summary": summary,
        "execution_history": history
    }


# Build LangGraph workflow
def build_rescue_graph():
    workflow = StateGraph(RescueAgentState)

    workflow.add_node("load_transaction", load_transaction)
    workflow.add_node("retrieve_evidence", retrieve_evidence)
    workflow.add_node("check_merchant_and_reversal", check_merchant_and_reversal)
    workflow.add_node("classify_evidence", classify_evidence)
    workflow.add_node("evaluate_policy", evaluate_policy)
    workflow.add_node("determine_next_action", determine_next_action)
    workflow.add_node("execute_action", execute_action)

    workflow.add_edge(START, "load_transaction")
    workflow.add_edge("load_transaction", "retrieve_evidence")
    workflow.add_edge("retrieve_evidence", "check_merchant_and_reversal")
    workflow.add_edge("check_merchant_and_reversal", "classify_evidence")
    workflow.add_edge("classify_evidence", "evaluate_policy")
    workflow.add_edge("evaluate_policy", "determine_next_action")
    workflow.add_edge("determine_next_action", "execute_action")
    workflow.add_edge("execute_action", END)

    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)


rescue_graph = build_rescue_graph()

async def run_rescue_investigation(transaction_id: str, user_id: str = "user_default_01") -> Dict[str, Any]:
    """
    Entry point to run the autonomous Raah Rescue investigation workflow.
    """
    initial_state: RescueAgentState = {
        "transaction_id": transaction_id,
        "user_id": user_id,
        "transaction_data": {},
        "payment_events": [],
        "merchant_confirmation": {},
        "reversal_status": {},
        "evidence_classification": "",
        "applicable_policy": {},
        "case_data": {},
        "next_action": "",
        "action_result": {},
        "execution_history": [],
        "is_terminal": False,
        "status_summary": ""
    }

    config = {"configurable": {"thread_id": f"rescue_{transaction_id}"}}
    final_state = await rescue_graph.ainvoke(initial_state, config=config)
    return final_state
