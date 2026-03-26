from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class OrderItemBase(BaseModel):
    item_id: int
    quantity: int
    price_at_time: float

class OrderItemResponse(OrderItemBase):
    id: int
    name: str 

    class Config:
        from_attributes = True

class OrderBase(BaseModel):
    status: str

class OrderResponse(BaseModel):
    id: int
    user_id: int
    status: str
    total_price: float
    created_at: datetime
    items: List[OrderItemResponse] = []

    class Config:
        from_attributes = True

class OrderUpdate(BaseModel):
    status: str