from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "STORAGE-SYSTEM"
    VERSION: str = "0.1.0"

    DATABASE_URL: str = "sqlite:///./storage.db"

    JWT_KEY: str = "2USE_OrIR8bGWUsNNou23s2Eq9-AWAEgR9sZTGoDZF4"
    JWT_ALG: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_PRE_PING: bool = True
    DB_ECHO: bool = False

    REDIS_URL: Optional[str] = None
    
settings = Settings()