import os

# Database
SQLALCHEMY_DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL","sqlite:///./blog.db")