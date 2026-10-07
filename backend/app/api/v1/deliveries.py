from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, UserRole
from app.models.order import Order, OrderStatus
from app.models.delivery import Delivery, DeliveryStatus
from app.schemas.delivery import DeliveryStatusUpdate, OTPVerificationRequest, DeliveryResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/deliveries", tags=["Delivery Logistics"])

@router.post("/update-status", response_model=DeliveryResponse)
def update_delivery_status(
    req: DeliveryStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    delivery = db.query(Delivery).filter(Delivery.order_id == req.order_id).first()
    if not delivery:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery record not found")

    delivery.delivery_status = req.delivery_status.value
    delivery.delivery_partner_id = current_user.id

    order = db.query(Order).filter(Order.id == req.order_id).first()

    if req.delivery_status == DeliveryStatus.IN_TRANSIT:
        delivery.pickup_at = datetime.now(timezone.utc)
        if order:
            order.status = OrderStatus.IN_TRANSIT
    elif req.delivery_status == DeliveryStatus.DELIVERED:
        delivery.delivered_at = datetime.now(timezone.utc)
        if order:
            order.status = OrderStatus.DELIVERED

    db.commit()
    db.refresh(delivery)
    return delivery

@router.post("/verify-otp", response_model=DeliveryResponse)
def verify_delivery_otp(
    req: OTPVerificationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    delivery = db.query(Delivery).filter(Delivery.order_id == req.order_id).first()
    if not delivery:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery record not found")

    if delivery.otp_code == req.otp_code.strip():
        delivery.otp_verified = True
        delivery.delivery_status = DeliveryStatus.DELIVERED
        delivery.delivered_at = datetime.now(timezone.utc)
        order = db.query(Order).filter(Order.id == req.order_id).first()
        if order:
            order.status = OrderStatus.DELIVERED
        db.commit()
        db.refresh(delivery)
        return delivery
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP code. Handover verification failed."
        )
