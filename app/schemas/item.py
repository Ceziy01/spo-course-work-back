from pydantic import BaseModel
from typing import Optional

class ItemBase(BaseModel):
    name: str
    description: Optional[str] = None
    article: str
    quantity: float
    unit: str
    shelf_life_days: Optional[int] = None
    price: float
    category_id: int
    warehouse_id: int

class ItemCreate(ItemBase):
    pass

class ItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    article: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    shelf_life_days: Optional[int] = None
    price: Optional[float] = None
    category_id: Optional[int] = None
    warehouse_id: Optional[int] = None

class ItemResponse(ItemBase):
    id: int
    category_name: Optional[str] = None
    warehouse_name: Optional[str] = None

    class Config:
        from_attributes = True