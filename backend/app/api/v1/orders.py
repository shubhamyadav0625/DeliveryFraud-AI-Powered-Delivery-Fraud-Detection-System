import random
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, UserRole
from app.models.order import Order, OrderItem, OrderStatus
from app.models.delivery import Delivery, DeliveryStatus
from app.schemas.order import OrderCreate, OrderResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/orders", tags=["Orders"])

@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    order_in: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not order_in.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order must contain at least one item"
        )
    
    total_amount = sum(item.unit_price * item.quantity for item in order_in.items)
    order_number = f"ORD-{random.randint(100000, 999999)}"

    order = Order(
        customer_id=current_user.id,
        order_number=order_number,
        total_amount=total_amount,
        status=OrderStatus.CREATED
    )
    db.add(order)
    db.flush()

    for item in order_in.items:
        order_item = OrderItem(
            order_id=order.id,
            sku=item.sku,
            item_name=item.item_name,
            quantity=item.quantity,
            unit_price=item.unit_price,
            expected_weight_grams=item.expected_weight_grams
        )
        db.add(order_item)

    otp_code = str(random.randint(1000, 9999))
    delivery = Delivery(
        order_id=order.id,
        delivery_status=DeliveryStatus.PENDING,
        otp_code=otp_code,
        otp_verified=False
    )
    db.add(delivery)

    db.commit()
    db.refresh(order)
    return order

@router.get("", response_model=List[OrderResponse])
def list_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == UserRole.ADMIN.value:
        return db.query(Order).order_by(Order.created_at.desc()).all()
    return db.query(Order).filter(Order.customer_id == current_user.id).order_by(Order.created_at.desc()).all()

@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if current_user.role != UserRole.ADMIN.value and order.customer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return order
