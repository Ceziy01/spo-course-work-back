from pydantic import BaseModel
from typing import Optional

class CreateUserRequest(BaseModel):
    username: str
    first_name: str
    last_name: str
    email: str
    password: str
    role: str
    
class Token(BaseModel):
    access_token: str
    token_type: str
    
class UsersMe(BaseModel):
    username: str
    first_name: str
    last_name: str
    email: str
    role: str
    
class UpdateUserRequest(BaseModel):
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    
class ResetPasswordRequest(BaseModel):
    new_password: str
    
class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str