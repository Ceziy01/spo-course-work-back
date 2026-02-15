from pydantic_settings import BaseSettings
from typing import Optional
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "STORAGE-SYSTEM"
    VERSION: str = "0.1.0"

    DATABASE_URL: str = os.getenv("DATABASE_URL")

    JWT_KEY: str = os.getenv("JWT_KEY")
    JWT_ALG: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_PRE_PING: bool = True
    DB_ECHO: bool = False

    REDIS_URL: Optional[str] = None
    
settings = Settings()