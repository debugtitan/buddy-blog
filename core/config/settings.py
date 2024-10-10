from pydantic_settings import BaseSettings
import os
from typing import Optional

class Settings(BaseSettings):
    # Database configuration
    # DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./blog.db")
    DATABASE_URL: str 
    
    # Convert postgres:// to postgresql:// for SQLAlchemy 1.4+
    # @property
    # def SQLALCHEMY_DATABASE_URL(self) -> str:
    #     if self.DATABASE_URL.startswith("postgres://"):
    #         return self.DATABASE_URL.replace("postgres://", "postgresql://", 1)
    #     return self.DATABASE_URL

    # Other settings
    GOOGLE_CLIENT_ID: str 
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    COOKIE_DOMAIN: Optional[str] = None
    IS_PRODUCTION: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = True

# Instantiate settings for use across the application
settings = Settings()