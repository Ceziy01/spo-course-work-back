from datetime import timedelta, datetime
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette import status
from database import SessionLocal
from config import settings
from models import Users
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError

router = APIRouter (
    prefix="/auth",
    tags=["auth"]
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")

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
    
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
db_dependency = Annotated[Session, Depends(get_db)]

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency, create_user_request: CreateUserRequest):
    create_user_model = Users(
        username=create_user_request.username,
        hashed_password=pwd_context.hash(create_user_request.password),
        is_admin=create_user_request.is_admin
    )
    
    db.add(create_user_model)
    db.commit()
    
@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], 
    db: db_dependency
    ):
    user = auth_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate user"
        )
    token = create_access_token(user.username, user.id, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": token, "token_type": "bearer"}  
    
def auth_user(username, password, db):
    user = db.query(Users).filter(Users.username == username).first()
    if not user: return False
    if not pwd_context.verify(password, user.hashed_password):
        return False
    return user

def create_access_token(username, id, exps: timedelta):
    encode = {"sub": username, "id": id}
    expires = datetime.utcnow() + exps
    encode.update({"exp": expires})
    return jwt.encode(encode, settings.JWT_KEY, algorithm=settings.JWT_ALG)

async def get_current_user(
    token: Annotated[str, Depends(oauth2_bearer)],
    db: db_dependency
):
    try:
        payload = jwt.decode(token, settings.JWT_KEY, algorithms=[settings.JWT_ALG])
        user_id: int = payload.get("id")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate user"
            )

        user = db.query(Users).filter(Users.id == user_id).first()

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        return user

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate user"
        )
        
@router.get("/users/me", response_model=UsersMe)
def read_users_me(current_user: Annotated[Users, Depends(get_current_user)]):
    return {
        "username": current_user.username,
        "is_admin": current_user.is_admin
    }
    
def require_admin(user: Annotated[Users, Depends(get_current_user)]):
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissions denied. Admins only"
        )
    return user

@router.get("/admin")
async def admin_panel(user: Annotated[Users, Depends(require_admin)]):
    return {"message": "Welcome admin"}

@router.post("/admin/create-user", status_code=status.HTTP_201_CREATED)
async def admin_create_user(
    create_user_request: CreateUserRequest,
    db: db_dependency,
    admin: Annotated[Users, Depends(require_admin)]
):
    user = Users(
        username=create_user_request.username,
        hashed_password=pwd_context.hash(create_user_request.password),
        is_admin=create_user_request.is_admin
    )
    
    db.add(user)
    db.commit()
    
    return {"message": "User created"}

@router.get("/admin/users")
async def get_all_users(db: db_dependency, admin: Annotated[Users, Depends(require_admin)]):
    users = db.query(Users).all()
    return [
        {
            "id": user.id,
            "username": user.username,
            "is_admin": user.is_admin
        }
        for user in users
    ]