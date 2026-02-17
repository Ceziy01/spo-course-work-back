from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
from config import settings

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