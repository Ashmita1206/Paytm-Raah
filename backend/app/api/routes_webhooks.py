import hmac
import hashlib
import json
from fastapi import APIRouter, Request, Header, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.config import settings
from app.models.payment import Transaction, PaymentEvent
from app.agents.rescue_agent import run_rescue_investigation

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

@router.post("/razorpay")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(None),
    db: Session = Depends(get_db)
):
    """
    Receives and verifies Razorpay Test Sandbox webhooks.
    Validates HMAC signature when secret is configured, updates transaction state,
    and invokes Raah Rescue for autonomous follow-up.
    """
    body_bytes = await request.body()
    body_str = body_bytes.decode("utf-8")

    # Verify signature if secret configured
    if settings.RAZORPAY_KEY_SECRET and x_razorpay_signature:
        expected_sig = hmac.new(
            settings.RAZORPAY_KEY_SECRET.encode("utf-8"),
            body_bytes,
            hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(expected_sig, x_razorpay_signature):
            raise HTTPException(status_code=400, detail="Invalid webhook signature")

    try:
        payload = json.loads(body_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_type = payload.get("event")
    payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
    order_id = payment_entity.get("order_id")

    if not order_id:
        return {"status": "IGNORED", "reason": "No order_id in webhook payload"}

    tx = db.query(Transaction).filter(Transaction.upi_ref_no == order_id).first()
    if tx:
        if event_type == "payment.captured":
            tx.status = "SUCCESS"
            ev = PaymentEvent(
                transaction_id=tx.id,
                event_type="BENEFICIARY_CONFIRMED",
                source="RAZORPAY_SANDBOX",
                provider_reference=payment_entity.get("id"),
                title="Webhook: Payment Captured (SANDBOX)",
                description="Razorpay sandbox confirmed payment capture.",
                verification_status="VERIFIED",
                is_synthetic=False
            )
            db.add(ev)
            db.commit()
            await run_rescue_investigation(tx.id, tx.user_id)
        elif event_type == "payment.failed":
            tx.status = "FAILED"
            ev = PaymentEvent(
                transaction_id=tx.id,
                event_type="PAYMENT_FAILED",
                source="RAZORPAY_SANDBOX",
                provider_reference=payment_entity.get("id"),
                title="Webhook: Payment Failed (SANDBOX)",
                description=payment_entity.get("error_description", "Payment gateway rejected transaction."),
                verification_status="VERIFIED",
                is_synthetic=False
            )
            db.add(ev)
            db.commit()

    return {"status": "PROCESSED", "event": event_type}
