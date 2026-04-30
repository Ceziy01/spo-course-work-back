from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PurchaseOrderBase(BaseModel):
    product_name: str
    quantity: int
    purchase_price: float
    supplier_id: int
    warehouse_id: int

class PurchaseOrderCreate(PurchaseOrderBase):
    pass

class PurchaseOrderUpdate(BaseModel):
    product_name: Optional[str] = None
    quantity: Optional[int] = None
    purchase_price: Optional[float] = None
    supplier_id: Optional[int] = None
    warehouse_id: Optional[int] = None
    status: Optional[str] = None

class PurchaseOrderResponse(PurchaseOrderBase):
    id: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    supplier_name: Optional[str] = None
    warehouse_name: Optional[str] = None

    class Config:
        from_attributes = True

class CompletePurchaseRequest(BaseModel):
    article: str
    description: Optional[str] = None
    unit: str
    shelf_life_days: Optional[int] = None
    selling_price: float
    category_id: Optional[int] = None
    image_url: Optional[str] = None