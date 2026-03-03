from pydantic import BaseModel

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