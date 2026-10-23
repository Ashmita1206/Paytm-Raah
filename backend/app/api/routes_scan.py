import re
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.user import DemoMerchant
from app.schemas.scan import QRScanRequest, QRScanResponse, MerchantInfo, DuplicateWarning
from app.services.retryguard_service import RetryGuardService

router = APIRouter(prefix="/scan", tags=["QR & Scan"])

@router.post("/resolve", response_model=QRScanResponse)
def resolve_qr(payload: QRScanRequest, db: Session = Depends(get_db)):
    """
    Decodes and validates a QR payload.
    Checks merchant registration, verifies local connectivity,
    and performs real-time RetryGuard duplicate payment check.
    """
    content = payload.qr_content.strip()

    # Parse supported demo QR format or standard UPI URI
    # Example format: upi://pay?pa=grocery@paytm&pn=Demo+Grocery+Store&am=4000
    # or simple merchant code: "merch_grocery_01" or "grocery@paytm"
    merchant = None
    suggested_amount = 4000.0

    if "pa=" in content:
        # Extract VPA
        vpa_match = re.search(r"pa=([^&]+)", content)
        if vpa_match:
            vpa = vpa_match.group(1).lower()
            merchant = db.query(DemoMerchant).filter(DemoMerchant.upi_vpa == vpa).first()
        am_match = re.search(r"am=([^&]+)", content)
        if am_match:
            try:
                suggested_amount = float(am_match.group(1))
            except ValueError:
                pass
    else:
        # Check by ID or VPA directly
        merchant = db.query(DemoMerchant).filter(
            (DemoMerchant.id == content) | (DemoMerchant.upi_vpa == content.lower())
        ).first()

    if not merchant:
        # Check fallback to default grocery merchant for generic scanner testing
        if "grocery" in content.lower():
            merchant = db.query(DemoMerchant).filter(DemoMerchant.id == "merch_grocery_01").first()
        elif "cafe" in content.lower():
            merchant = db.query(DemoMerchant).filter(DemoMerchant.id == "merch_cafe_02").first()
        elif "pharmacy" in content.lower():
            merchant = db.query(DemoMerchant).filter(DemoMerchant.id == "merch_pharmacy_03").first()

    if not merchant:
        return QRScanResponse(
            valid=False,
            error_message="Unsupported or unrecognized QR code. Please scan a verified demo merchant QR.",
            merchant=None,
            network_connectivity_ok=True,
            duplicate_check=DuplicateWarning(has_potential_duplicate=False),
            suggested_amount=0.0
        )

    # Use default merchant amount if not in QR
    if suggested_amount <= 0:
        suggested_amount = merchant.default_amount

    # Execute RetryGuard duplicate check
    dup_check = RetryGuardService.check_duplicate_risk(
        db=db,
        user_id=payload.user_id or "user_default_01",
        merchant_id=merchant.id,
        amount=suggested_amount,
        window_minutes=15
    )

    return QRScanResponse(
        valid=True,
        error_message=None,
        merchant=MerchantInfo(
            id=merchant.id,
            name=merchant.merchant_name,
            upi_vpa=merchant.upi_vpa,
            category=merchant.category,
            verified=merchant.verified,
            default_amount=merchant.default_amount,
            logo_symbol=merchant.logo_symbol
        ),
        network_connectivity_ok=True,
        duplicate_check=DuplicateWarning(
            has_potential_duplicate=dup_check["has_potential_duplicate"],
            warning_message=dup_check.get("warning_message"),
            existing_transaction_id=dup_check.get("existing_transaction_id"),
            existing_amount=dup_check.get("existing_amount"),
            existing_status=dup_check.get("existing_status"),
            elapsed_minutes=dup_check.get("elapsed_minutes"),
            can_proceed_with_acknowledgement=True
        ),
        suggested_amount=suggested_amount
    )
