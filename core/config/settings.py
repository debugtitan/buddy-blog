from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    SQLALCHEMY_DATABASE_URL: str = "sqlite:///./blog.db"   
    GOOGLE_CLIENT_ID: str 
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"

# Instantiate settings for use across the application
settings = Settings()
