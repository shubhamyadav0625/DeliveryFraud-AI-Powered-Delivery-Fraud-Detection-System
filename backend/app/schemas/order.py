from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

class OrderItemCreate(BaseModel):
    sku: str
    item_name: str
    quantity: int = 1
    unit_price: float
    expected_weight_grams: float = 100.0

class OrderItemResponse(OrderItemCreate):
    id: str
    order_id: str

    model_config = ConfigDict(from_attributes=True)

class OrderCreate(BaseModel):
    items: List[OrderItemCreate]

class OrderResponse(BaseModel):
    id: str
    customer_id: str
    order_number: str
    total_amount: float
    status: str
    created_at: datetime
    items: List[OrderItemResponse]

    model_config = ConfigDict(from_attributes=True)
