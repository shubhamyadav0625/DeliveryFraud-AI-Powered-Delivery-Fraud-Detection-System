import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base

import enum

class ClaimStatus(str, enum.Enum):
    SUBMITTED = "SUBMITTED"
    IN_ANALYSIS = "IN_ANALYSIS"
    APPROVED = "APPROVED"
    VERIFY_REQUESTED = "VERIFY_REQUESTED"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    REJECTED = "REJECTED"

class ClaimType(str, enum.Enum):
    MISSING_ITEM = "MISSING_ITEM"
    WRONG_ITEM = "WRONG_ITEM"
    WRONG_QUANTITY = "WRONG_QUANTITY"
    DAMAGED_ITEM = "DAMAGED_ITEM"
    EXPIRED_ITEM = "EXPIRED_ITEM"
    WRONG_ORDER = "WRONG_ORDER"
    ENTIRE_ORDER_MISSING = "ENTIRE_ORDER_MISSING"
    BILLING_ISSUE = "BILLING_ISSUE"
    MISSING_PROMO = "MISSING_PROMO"
    OTHER = "OTHER"

class Claim(Base):
    __tablename__ = "claims"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    claim_number = Column(String(100), unique=True, nullable=False, index=True)
    status = Column(String(50), nullable=False, default=ClaimStatus.SUBMITTED, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    order = relationship("Order", back_populates="claims")
    customer = relationship("User", back_populates="claims", foreign_keys=[customer_id])
    claim_items = relationship("ClaimItem", back_populates="claim", cascade="all, delete-orphan")
    evidence_files = relationship("EvidenceFile", back_populates="claim", cascade="all, delete-orphan")
    risk_assessment = relationship("RiskAssessment", back_populates="claim", uselist=False, cascade="all, delete-orphan")
    decisions = relationship("Decision", back_populates="claim", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="claim", cascade="all, delete-orphan")

class ClaimItem(Base):
    __tablename__ = "claim_items"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    claim_id = Column(String(36), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False, index=True)
    order_item_id = Column(String(36), ForeignKey("order_items.id", ondelete="CASCADE"), nullable=False)
    claim_type = Column(String(50), nullable=False, default=ClaimType.MISSING_ITEM)
    claimed_quantity = Column(Integer, nullable=False, default=1)
    customer_reason = Column(Text, nullable=True)

    # Relationships
    claim = relationship("Claim", back_populates="claim_items")
    order_item = relationship("OrderItem", back_populates="claim_items")
