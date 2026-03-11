from pydantic import BaseModel
from typing import Optional

class WarehouseBase(BaseModel):
    name: str
    address: str

class WarehouseCreate(WarehouseBase):
    pass

class WarehouseUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None

class WarehouseResponse(WarehouseBase):
    id: int

    class Config:
        from_attributes = True