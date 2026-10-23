from typing import Optional
from pydantic import BaseModel

class QRScanRequest(BaseModel):
    qr_content: str
    user_id: Optional[str] = "user_default_01"

class MerchantInfo(BaseModel):
    id: str
    name: str
    upi_vpa: str
    category: str
    verified: bool
    default_amount: float
    logo_symbol: str

class DuplicateWarning(BaseModel):
    has_potential_duplicate: bool
    warning_message: Optional[str] = None
    existing_transaction_id: Optional[str] = None
    existing_amount: Optional[float] = None
    existing_status: Optional[str] = None
    elapsed_minutes: Optional[int] = None
    can_proceed_with_acknowledgement: bool = True

class QRScanResponse(BaseModel):
    valid: bool
    error_message: Optional[str] = None
    merchant: Optional[MerchantInfo] = None
    network_connectivity_ok: bool = True
    duplicate_check: DuplicateWarning
    suggested_amount: float = 4000.0
