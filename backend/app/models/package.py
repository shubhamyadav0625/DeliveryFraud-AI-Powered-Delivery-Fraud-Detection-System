import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base

class Package(Base):
    __tablename__ = "packages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), unique=True, nullable=False)
    package_barcode = Column(String(100), unique=True, nullable=False)
    total_expected_weight_grams = Column(Float, nullable=False)
    measured_weight_grams = Column(Float, nullable=False)
    seal_intact = Column(Boolean, default=True)
    packed_at = Column(DateTime, default=datetime.utcnow)

    order = relationship("Order", back_populates="package")
    packing_events = relationship("PackingEvent", back_populates="package", cascade="all, delete-orphan")

class PackingEvent(Base):
    __tablename__ = "packing_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    package_id = Column(String(36), ForeignKey("packages.id", ondelete="CASCADE"), nullable=False, index=True)
    sku = Column(String(100), nullable=False)
    scanned = Column(Boolean, default=True)
    scanned_at = Column(DateTime, default=datetime.utcnow)
    station_id = Column(String(100), nullable=False, default="STATION-01")

    package = relationship("Package", back_populates="packing_events")
