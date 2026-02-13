from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.repositories.user_repository import user_repository
from app.core.security import verfy_password, create_access_token, create_refresh_token, decode_token
from app.schemas.user import UserCreate
from app.schemas.token import Token
from datetime import timedelta
from app.core.config import settings

class AuthService:
    def authenticate_user(self, db: Session, username: str, password: str):
        user = user_repository.get_by_email(db, username)
        if not user: 
            user = user_repository.get_by_username(db, username)
            return None

        if not verfy_password(password, user.hashed_password): return None
        
        return user
    
    def create_tokens(self, user_id: int):
        access_token = create_access_token(
            data = {"sub": str(user_id)},
            expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        refresh_token = create_refresh_token(
            data = {"sub": str(user_id)}
        )
        
    def refresh_access_token(self, refresh_token: str):
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
            
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
            
        return self.create_tokens(int(user_id))
    
    def register_user(self, db: Session, user_data: UserCreate):
        if user_repository.get_by_email(db, user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        if user_repository.get_by_username(db, user_data.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
            
        user = user_repository.create(db, user_data)
        return user
    
auth_service = AuthService()