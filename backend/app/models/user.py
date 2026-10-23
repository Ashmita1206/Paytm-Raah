import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database.session import Base
from app.utils.time_utils import utcnow

class User(Base):
    __tablename__ = "users"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    phone = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    upi_vpa = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    transactions = relationship("Transaction", back_populates="user")
    cases = relationship("ResolutionCase", back_populates="user")
    chat_sessions = relationship("ChatSession", back_populates="user")
    notifications = relationship("Notification", back_populates="user")


class DemoMerchant(Base):
    __tablename__ = "demo_merchants"

    id = Column(String(64), primary_key=True)
    merchant_name = Column(String(120), nullable=False)
    upi_vpa = Column(String(100), unique=True, nullable=False)
    category = Column(String(50), default="GROCERY")
    verified = Column(Boolean, default=True)
    active = Column(Boolean, default=True)
    logo_symbol = Column(String(10), default="🛒")
    default_amount = Column(Float, default=4000.0)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    transactions = relationship("Transaction", back_populates="merchant")


class MerchantOrder(Base):
    __tablename__ = "merchant_orders"

    id = Column(String(64), primary_key=True, default=lambda: f"order_{uuid.uuid4().hex[:12]}")
    merchant_id = Column(String(64), ForeignKey("demo_merchants.id"), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="INR")
    status = Column(String(30), default="CREATED")  # CREATED, PAID, EXPIRED, CANCELLED
    item_description = Column(String(255), default="Demo purchase")
    created_at = Column(DateTime(timezone=True), default=utcnow)
