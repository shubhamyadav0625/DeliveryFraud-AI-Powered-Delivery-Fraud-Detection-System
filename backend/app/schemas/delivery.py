from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.models.delivery import DeliveryStatus

class DeliveryStatusUpdate(BaseModel):
    order_id: str
    delivery_status: DeliveryStatus

class OTPVerificationRequest(BaseModel):
    order_id: str
    otp_code: str

class DeliveryResponse(BaseModel):
    id: str
    order_id: str
    delivery_partner_id: Optional[str] = None
    delivery_status: str
    otp_code: str
    otp_verified: bool
    pickup_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
