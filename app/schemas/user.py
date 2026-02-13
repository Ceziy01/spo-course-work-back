from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    phone: str
    username: str
    full_name: Optional[str] = None
    is_active: Optional[bool] = True
    is_admin: bool = False
    
class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    
class UserInDB(UserBase):
    id: int
    created_at:datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attrib = True
    
class User(UserInDB):
    pass