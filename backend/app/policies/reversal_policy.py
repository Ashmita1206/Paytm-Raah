from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from app.utils.time_utils import utcnow, ensure_naive

class RegulatoryPolicyEngine:
    """
    Deterministic implementation of RBI Harmonisation of Turn Around Time (TAT)
    and customer compensation for failed transactions (Circular DPSS.CO.PD No.629/02.01.014/2019-20).
    
    CRITICAL: Never generate a made-up exact money-arrival date.
    Explain that this is a regulatory resolution deadline, not a guaranteed credit timestamp.
    """

    POLICY_REGISTRY = {
        "UPI_P2M": {
            "policy_id": "RBI_UPI_P2M_2020",
            "name": "RBI TAT Harmonisation — UPI Merchant (P2M)",
            "description": "Customer account debited but transaction confirmation not received at merchant location.",
            "tat_working_days": 5,
            "tat_hours": 120,
            "auto_reversal_required": True,
            "compensation_per_day_inr": 100.0,
            "authority": "Reserve Bank of India (RBI)",
            "circular_ref": "DPSS.CO.PD No.629/02.01.014/2019-20",
            "disclaimer": "This is a regulatory resolution deadline established by RBI guidelines, not a guaranteed credit timestamp. Bank settlement networks may resolve the transaction earlier or require multi-party reconciliation."
        },
        "UPI_P2P": {
            "policy_id": "RBI_UPI_P2P_2020",
            "name": "RBI TAT Harmonisation — UPI Person-to-Person (P2P)",
            "description": "Customer account debited but beneficiary customer account not credited.",
            "tat_working_days": 1,
            "tat_hours": 24,
            "auto_reversal_required": True,
            "compensation_per_day_inr": 100.0,
            "authority": "Reserve Bank of India (RBI)",
            "circular_ref": "DPSS.CO.PD No.629/02.01.014/2019-20",
            "disclaimer": "This is a regulatory resolution deadline established by RBI guidelines (T+1), not a guaranteed credit timestamp."
        },
        "PRE_DEBIT_FAILURE": {
            "policy_id": "POLICY_PRE_DEBIT_REJECT",
            "name": "Standard Payment Gateway Failure Policy",
            "description": "Payment failed prior to customer account debit (e.g. incorrect PIN, expired session).",
            "tat_working_days": 0,
            "tat_hours": 0,
            "auto_reversal_required": False,
            "compensation_per_day_inr": 0.0,
            "authority": "Standard Payment Switch Protocol",
            "circular_ref": "N/A",
            "disclaimer": "No funds debited. Customer may re-initiate payment immediately without duplicate risk."
        }
    }

    @classmethod
    def evaluate_transaction(cls, category: str, transaction_timestamp: datetime) -> Dict[str, Any]:
        """
        Determines applicable regulatory turnaround time and policy parameters.
        """
        norm_cat = "UPI_P2M"
        if "P2P" in category.upper():
            norm_cat = "UPI_P2P"
        elif "PRE_DEBIT" in category.upper() or "FAILED_BEFORE_DEBIT" in category.upper():
            norm_cat = "PRE_DEBIT_FAILURE"

        policy = cls.POLICY_REGISTRY[norm_cat]
        tx_ts = ensure_naive(transaction_timestamp) or utcnow()
        deadline = tx_ts + timedelta(hours=policy["tat_hours"])
        
        now = utcnow()
        is_overdue = now > deadline if policy["tat_hours"] > 0 else False
        overdue_days = max(0, (now - deadline).days) if is_overdue else 0
        potential_compensation = overdue_days * policy["compensation_per_day_inr"]

        return {
            "policy_id": policy["policy_id"],
            "policy_name": policy["name"],
            "description": policy["description"],
            "tat_working_days": policy["tat_working_days"],
            "tat_hours": policy["tat_hours"],
            "regulatory_deadline": deadline,
            "regulatory_deadline_iso": deadline.isoformat(),
            "regulatory_deadline_text": f"T+{policy['tat_working_days']} working days ({deadline.strftime('%d %b %Y, %I:%M %p')})",
            "disclaimer": policy["disclaimer"],
            "compensation_per_day_inr": policy["compensation_per_day_inr"],
            "is_overdue": is_overdue,
            "overdue_days": overdue_days,
            "potential_compensation_inr": potential_compensation,
            "compensation_eligible_for_verification": is_overdue and potential_compensation > 0,
            "auto_reversal_mandated": policy["auto_reversal_required"]
        }
