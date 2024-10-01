# routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie
from fastapi.security import OAuth2PasswordBearer
from core.db import db_dependacy
from core.models.users import User
from core.schemas.users import UserCreate, UserRetrieve
from core.config.settings import settings
from pydantic import BaseModel
import requests
from jose import JWTError, jwt
from datetime import datetime, timedelta
import secrets

auth_router = APIRouter(tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class TokenData(BaseModel):
    token: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserRetrieve

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 30

def get_current_user(db: db_dependacy, token: str = Depends(oauth2_scheme) ):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decode the JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")
        if user_email is None:
            raise credentials_exception
        
        # Fetch the user from the database
        user = db.query(User).filter(User.email == user_email).first()
        if user is None:
            raise credentials_exception
        return user
    except JWTError:
        raise credentials_exception

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token():
    return secrets.token_urlsafe(32)

@auth_router.post("/auth/google", response_model=Token)
async def google_auth(token_data: TokenData, response: Response, db: db_dependacy):
    try:
        print(f"Received Google token: {token_data.token[:10]}...")  # Print first 10 chars for security
        
        # Use the Google ID to fetch user info
        google_response = requests.get(f'https://www.googleapis.com/oauth2/v3/userinfo?access_token={token_data.token}')
        if google_response.status_code != 200:
            print(f"Google API error: {google_response.status_code} - {google_response.text}")
            raise ValueError(f"Failed to fetch user info: {google_response.status_code}")
        
        user_data = google_response.json()
        print(f"Received user data: {user_data}")
        
        user_email = user_data['email']
        user_name = user_data.get('name', '')
        user_picture = user_data.get('picture', '')


        # Check if user exists, if not create a new user
        user = db.query(User).filter(User.email == user_email).first()
        if not user:
            print(f"Creating new user with email: {user_email}")
            new_user = User(email=user_email, name=user_name, picture=user_picture)
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            user = new_user
        else:
            print(f"Existing user found: {user.email}")

        # Create access and refresh tokens
        access_token = create_access_token({"sub": user.email})
        refresh_token = create_refresh_token()

        # Store refresh token in the database
        user.refresh_token = refresh_token
        db.commit()

        # Set refresh token in an HTTP-only cookie
        response.set_cookie(
            key="refresh_token", 
            value=refresh_token,
            httponly=True,
            secure=True,  # Use this in production with HTTPS
            samesite='lax',
            max_age=60 * 60 * 24 * REFRESH_TOKEN_EXPIRE_DAYS,  # 30 days
            domain=None,  # Set this to your domain in production
            path="/"
        )

        print(f"Authentication successful for user: {user.email}")
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": UserRetrieve.model_validate(user)
        }

    except Exception as e:
        print(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


@auth_router.post("/auth/refresh", response_model=Token)
async def refresh_token(response: Response, db: db_dependacy, refresh_token: str = Cookie(None)):
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token missing")
    
    try:
        user = db.query(User).filter(User.refresh_token == refresh_token).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

        # Create new access and refresh tokens
        new_access_token = create_access_token({"sub": user.email})
        new_refresh_token = create_refresh_token()

        # Update refresh token in the database
        user.refresh_token = new_refresh_token
        db.commit()

        # Set new refresh token in an HTTP-only cookie
        response.set_cookie(
            key="refresh_token", 
            value=new_refresh_token,
            httponly=True,
            secure=True,  # Use this in production with HTTPS
            samesite='lax',
            max_age=60 * 60 * 24 * REFRESH_TOKEN_EXPIRE_DAYS,  # 30 days
            domain=None,  # Set this to your domain in production
            path="/"
        )

        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "user": UserRetrieve.model_validate(user)
        }

    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

@auth_router.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie(
        key="refresh_token",
        path="/",
        domain=None,  # Set this to your domain in production
    )
    return {"message": "Successfully logged out"}