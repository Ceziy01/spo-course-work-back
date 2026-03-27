from datetime import timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException

from db.models.user import Users
from core.security import verify_password, hash_password, create_access_token
from config import settings

def authenticate_user(username: str, password: str, db: Session):
    user = db.query(Users).filter(Users.username == username).first()
    if not user:
        verify_password(password, settings.FAKE_HASH)
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    return user

def create_user(username: str, first_name: str, last_name: str, email: str, password: str, role: str, db: Session):
    if len(password) < 8:
        raise HTTPException(
            status_code=400, 
            detail="Password too short"
            )
    user = Users(
        username=username,
        first_name=first_name,
        last_name=last_name,
        email=email,
        hashed_password=hash_password(password),
        role=role
    )
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except InterruptedError:
        db.rollback()
        raise HTTPException(400, "Username already exists")
    return user


def login_user(user, db: Session):
    return create_access_token(
        user.username,
        user.id,
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
