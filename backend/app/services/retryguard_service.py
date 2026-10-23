from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.config import settings
from app.models.payment import Transaction, PaymentEvent
from app.utils.time_utils import utcnow, ensure_naive

class RetryGuardService:
    """
    Intelligent Duplicate Payment Protection Engine.
    Detects concurrent or recent unconfirmed payment attempts for the same merchant
    and user within a sliding time window (default 15 minutes) with amount proximity checks.
    """

    @classmethod
    def check_duplicate_risk(
        cls,
        db: Session,
        user_id: str,
        merchant_id: str,
        amount: float,
        window_minutes: Optional[int] = None
    ) -> Dict[str, Any]:
        win = window_minutes or settings.RETRYGUARD_WINDOW_MINUTES
        window_start = utcnow() - timedelta(minutes=win)

        # Look for recent transactions that are NOT in a clear terminal state (e.g. OUTCOME_UNKNOWN, DEBIT_REPORTED, PENDING)
        candidates = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.merchant_id == merchant_id,
            Transaction.status.in_(["OUTCOME_UNKNOWN", "DEBIT_REPORTED", "PENDING"]),
            Transaction.created_at >= window_start
        ).order_by(Transaction.created_at.desc()).all()

        for candidate in candidates:
            # Check amount proximity (within 5% or exact match)
            diff = abs(candidate.amount - amount)
            ratio = diff / max(candidate.amount, 1.0)

            if ratio <= settings.RETRYGUARD_SIMILARITY_PERCENT:
                # Potential duplicate detected!
                cand_created = ensure_naive(candidate.created_at)
                elapsed = int((utcnow() - cand_created).total_seconds() / 60) if cand_created else 1
                return {
                    "has_potential_duplicate": True,
                    "existing_transaction_id": candidate.id,
                    "existing_amount": candidate.amount,
                    "existing_status": candidate.status,
                    "elapsed_minutes": max(1, elapsed),
                    "warning_message": (
                        f"RetryGuard Alert: Your previous ₹{candidate.amount:,.2f} payment to this merchant "
                        f"initiated {elapsed} minute(s) ago is still unconfirmed. "
                        f"Please verify its outcome before paying again to avoid duplicate bank debits."
                    ),
                    "can_proceed_with_acknowledgement": True
                }

        return {
            "has_potential_duplicate": False,
            "warning_message": None,
            "existing_transaction_id": None,
            "can_proceed_with_acknowledgement": True
        }
