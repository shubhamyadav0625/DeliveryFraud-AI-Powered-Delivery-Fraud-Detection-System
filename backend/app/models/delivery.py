import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base

import enum

class DeliveryStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"

class Delivery(Base):
    __tablename__ = "deliveries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), unique=True, nullable=False)
    delivery_partner_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    delivery_status = Column(String(50), nullable=False, default=DeliveryStatus.PENDING)
    otp_code = Column(String(10), nullable=False)
    otp_verified = Column(Boolean, default=False)
    pickup_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)

    # Relationships
    order = relationship("Order", back_populates="delivery")
    delivery_partner = relationship("User", back_populates="deliveries")
