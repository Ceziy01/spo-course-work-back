from pydantic import BaseModel

class CreateUserRequest(BaseModel):
    username: str
    password: str
    is_admin: bool
    
class Token(BaseModel):
    access_token: str
    token_type: str
    
class UsersMe(BaseModel):
    username: str
    is_admin: bool