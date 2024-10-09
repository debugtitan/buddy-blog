import os
from sqlalchemy import create_engine, text
import psycopg2
from urllib.parse import urlparse

def test_detailed_connection():
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        return "DATABASE_URL is not set"
    
    try:
        # Parse the URL
        parsed = urlparse(database_url)
        
        print(f"Attempting to connect to:")
        print(f"Host: {parsed.hostname}")
        print(f"Port: {parsed.port}")
        print(f"Database: {parsed.path[1:]}")  # Remove leading slash
        print(f"Username: {parsed.username}")
        
        # Try SQLAlchemy connection
        engine = create_engine(database_url)
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version()"))
            version = result.scalar()
            
        return f"Connection successful! Database version: {version}"
    
    except Exception as e:
        return f"Connection failed: {str(e)}"

if __name__ == "__main__":
    print(test_detailed_connection())