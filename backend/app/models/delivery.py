import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base

class DeliveryStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"

class DeliveryEventType(str, enum.Enum):
    ORDER_CREATED = "ORDER_CREATED"
    ITEM_SCANNED = "ITEM_SCANNED"
    PACKED = "PACKED"
    PACKAGE_WEIGHT_RECORDED = "PACKAGE_WEIGHT_RECORDED"
    HANDOVER = "HANDOVER"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    DELIVERY_ATTEMPT = "DELIVERY_ATTEMPT"
    OTP_VERIFIED = "OTP_VERIFIED"
    DELIVERED = "DELIVERED"
    CLAIM_CREATED = "CLAIM_CREATED"
    EVIDENCE_SUBMITTED = "EVIDENCE_SUBMITTED"
    ANALYSIS_COMPLETED = "ANALYSIS_COMPLETED"
    VERIFICATION_REQUESTED = "VERIFICATION_REQUESTED"
    INVESTIGATION_STARTED = "INVESTIGATION_STARTED"
    RESOLVED = "RESOLVED"

class Delivery(Base):
    __tablename__ = "deliveries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), unique=True, nullable=False)
    delivery_partner_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    delivery_status = Column(String(50), nullable=False, default=DeliveryStatus.PENDING.value)
    otp_code = Column(String(10), nullable=False)
    otp_verified = Column(Boolean, default=False)
    pickup_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)

    order = relationship("Order", back_populates="delivery")
    delivery_partner = relationship("User", back_populates="deliveries")

class DeliveryEvent(Base):
    __tablename__ = "delivery_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    actor = Column(String(100), nullable=False, default="SYSTEM")
    location = Column(String(255), nullable=True)
    metadata_json = Column(String(1000), nullable=False, default="{}")
    timestamp = Column(DateTime, default=datetime.utcnow)

    order = relationship("Order")
    customer = relationship("User")
