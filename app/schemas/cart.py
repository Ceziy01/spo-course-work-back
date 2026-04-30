from pydantic import BaseModel
from typing import Optional

class CartItemCreate(BaseModel):
    item_id: int
    quantity: int = 1

class CartItemUpdate(BaseModel):
    quantity: int

class CartItemResponse(BaseModel):
    id: int
    item_id: int
    name: str
    article: str
    quantity: int
    price: float
    image_url: Optional[str] = None
    total_price: float

    class Config:
        from_attributes = True