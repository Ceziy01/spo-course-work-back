from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
from config import settings
from sqlalchemy.orm import Session
import secrets

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=13)

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str):
    return pwd_context.verify(password, hashed)

def create_access_token(username, id, exps: timedelta):
    encode = {"sub": username, "id": id}
    expires = datetime.utcnow() + exps
    encode.update({"exp": expires})
    return jwt.encode(encode, settings.JWT_KEY, algorithm=settings.JWT_ALG)

def generate_refresh_token() -> str:
    return secrets.token_hex(32)

def create_refresh_token(user_id: int, db: Session):
    from db.models.refresh_token import RefreshToken

    db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
        RefreshToken.expires_at < datetime.utcnow()
    ).delete()

    token_value = generate_refresh_token()
    expires_at = datetime.utcnow() + timedelta(days=30)

    refresh_token = RefreshToken(
        user_id=user_id,
        token=token_value,
        expires_at=expires_at
    )
    db.add(refresh_token)
    db.commit()
    db.refresh(refresh_token)
    return token_value

def verify_refresh_token(token: str, db: Session):
    from db.models.refresh_token import RefreshToken

    refresh_record = db.query(RefreshToken).filter(
        RefreshToken.token == token,
        RefreshToken.expires_at > datetime.utcnow()
    ).first()
    return refresh_record.user_id if refresh_record else None