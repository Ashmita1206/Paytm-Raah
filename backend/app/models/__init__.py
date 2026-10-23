from app.database.session import Base, engine
from app.models.user import User, DemoMerchant, MerchantOrder
from app.models.payment import Transaction, PaymentEvent, ProviderObservation
from app.models.case import ResolutionCase, CaseActionLog, ScheduledFollowup, HumanApprovalRequest
from app.models.incident import IncidentRecord, IncidentTransactionLink
from app.models.chat import ChatSession, ChatMessage
from app.models.notification import Notification

def init_db():
    Base.metadata.create_all(bind=engine)

__all__ = [
    "Base",
    "init_db",
    "User",
    "DemoMerchant",
    "MerchantOrder",
    "Transaction",
    "PaymentEvent",
    "ProviderObservation",
    "ResolutionCase",
    "CaseActionLog",
    "ScheduledFollowup",
    "HumanApprovalRequest",
    "IncidentRecord",
    "IncidentTransactionLink",
    "ChatSession",
    "ChatMessage",
    "Notification",
]
