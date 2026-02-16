from datetime import timedelta
from sqlalchemy.orm import Session

from models import Users
from core.security import verify_password, hash_password, create_access_token
from config import settings


def authenticate_user(username: str, password: str, db: Session):
    user = db.query(Users).filter(Users.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_user(username: str, password: str, is_admin: bool, db: Session):
    user = Users(
        username=username,
        hashed_password=hash_password(password),
        is_admin=is_admin
    )
    db.add(user)
    db.commit()
    return user


def login_user(user, db: Session):
    return create_access_token(
        user.username,
        user.id,
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
