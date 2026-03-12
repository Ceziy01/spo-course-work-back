from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os, sys
from pathlib import Path

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "STORAGE-SYSTEM"
    VERSION: str = "0.1.0"

    DATABASE_URL: str = os.getenv("DATABASE_URL")

    JWT_KEY: str = os.getenv("JWT_KEY")
    JWT_ALG: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    FAKE_HASH: str = "$2b$12$KbQiVbF7z0J8yF8vYx9m7e7VYh3Y7V5W7y7V5W7y7V5W7y7V5W7y7"

if not Path(".env").exists():
    raise FileNotFoundError(".env не найден!")

settings = Settings()

if not settings.DATABASE_URL:
    raise RuntimeError("DATABASE_URL не задан")

if not settings.JWT_KEY:
    raise RuntimeError("JWT_KEY не задан")