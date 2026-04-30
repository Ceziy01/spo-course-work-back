from pydantic import BaseModel
from typing import Optional

class SupplierBase(BaseModel):
    name: str
    address: str

class SupplierCreate(SupplierBase):
    pass

class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None

class SupplierResponse(SupplierBase):
    id: int

    class Config:
        from_attributes = True