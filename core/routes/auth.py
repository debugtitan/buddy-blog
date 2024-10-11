# routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie
from fastapi.security import OAuth2PasswordBearer
from core.db import db_dependacy
from core.models.users import User
from core.schemas.users import UserRetrieve
from core.config.settings import settings
from pydantic import BaseModel
import httpx
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
import secrets
from contextlib import contextmanager

@contextmanager
def get_httpx_client():
    client = httpx.Client()
    try:
        yield client
    finally:
        client.close()

auth_router = APIRouter(tags=["Authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class TokenData(BaseModel):
    token: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserRetrieve

# Helper function to set cookies
def set_auth_cookies(response: Response, access_token: str, refresh_token: str):
    cookie_settings = {
        "httponly": True,
        "secure": settings.IS_PRODUCTION,
        "samesite": 'lax',
        "domain": settings.COOKIE_DOMAIN,
        "path": "/"
    }
    
    print(f"Setting cookies with domain: {settings.COOKIE_DOMAIN}")
    
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=60 * settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        **cookie_settings
    )
    
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=60 * 60 * 24 * 30,  # 30 days
        **cookie_settings
    )

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token():
    return secrets.token_urlsafe(32)

def get_current_user(
    db: db_dependacy,
    access_token: Optional[str] = Cookie(None),
    refresh_token: Optional[str] = Cookie(None)
):
    print(f"Received access_token: {access_token}")
    print(f"Received refresh_token: {refresh_token}")
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not access_token and not refresh_token:
        print(f"{credentials_exception} - No token provided in Cookies")
        raise credentials_exception
    
    try:
        user = None
        if access_token:
            payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_email = payload.get("sub")
            if user_email:
                user = db.query(User).filter(User.email == user_email).first()
        
        if not user and refresh_token:
            user = db.query(User).filter(User.refresh_token == refresh_token).first()
        
        if not user:
            print(f"{credentials_exception} - User not found")
            raise credentials_exception
            
        return user
    except JWTError:
        print(f"{credentials_exception} - Invalid JWT token")
        raise credentials_exception

@auth_router.get("/auth/me", response_model=UserRetrieve)
async def get_current_user_info(
    response: Response,
    current_user: User = Depends(get_current_user),
    db: db_dependacy = db_dependacy,
):
    # Create a new access token
    access_token = create_access_token({"sub": current_user.email})
    refresh_token = current_user.refresh_token or create_refresh_token()
    
    # Use helper function to set cookies
    set_auth_cookies(response, access_token, refresh_token)
    
    return current_user

@auth_router.post("/auth/google", response_model=Token)
async def google_auth(token_data: TokenData, response: Response, db: db_dependacy):
    try:
        print(f"Starting Google authentication process")
        print(f"Production mode: {settings.IS_PRODUCTION}")
        print(f"Cookie domain: {settings.COOKIE_DOMAIN}")
        
        with get_httpx_client() as client:
            google_response = client.get(
                'https://www.googleapis.com/oauth2/v3/userinfo',
                params={'access_token': token_data.token},
                timeout=5.0
            )
        
        if google_response.status_code != 200:
            print(f"Google API error: {google_response.status_code} - {google_response.text}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Failed to verify Google token: {google_response.status_code}"
            )
        
        user_data = google_response.json()
        print(f"Received user data from Google: {user_data}")
        
        user_email = user_data.get('email')
        if not user_email:
            raise ValueError("Email not provided by Google")
        
        user_name = user_data.get('name', '')
        user_picture = user_data.get('picture', '')

        user = db.query(User).filter(User.email == user_email).first()
        if not user:
            print(f"Creating new user with email: {user_email}")
            user = User(
                email=user_email,
                name=user_name,
                picture=user_picture
            )
            db.add(user)
        else:
            print(f"Updating existing user: {user_email}")
            user.name = user_name
            user.picture = user_picture
        
        access_token = create_access_token({"sub": user_email})
        refresh_token = create_refresh_token()
        
        user.refresh_token = refresh_token
        db.commit()
        db.refresh(user)

        # Use helper function to set cookies
        set_auth_cookies(response, access_token, refresh_token)
        
        print(f"Authentication successful for user: {user_email}")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": UserRetrieve.model_validate(user)
        }

    except httpx.RequestError as e:
        print(f"Network error during Google authentication: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to connect to Google: {str(e)}"
        )
    except Exception as e:
        print(f"Unexpected error during authentication: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@auth_router.post("/auth/refresh", response_model=Token)
async def refresh_token(
    response: Response,
    db: db_dependacy,
    refresh_token: str = Cookie(None)
):
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing"
        )
    
    try:
        user = db.query(User).filter(User.refresh_token == refresh_token).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        # Create new tokens
        new_access_token = create_access_token({"sub": user.email})
        new_refresh_token = create_refresh_token()

        # Update refresh token in the database
        user.refresh_token = new_refresh_token
        db.commit()

        # Use helper function to set cookies
        set_auth_cookies(response, new_access_token, new_refresh_token)

        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "user": UserRetrieve.model_validate(user)
        }

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

@auth_router.post("/auth/logout")
async def logout(response: Response):
    cookie_settings = {
        "httponly": True,
        "secure": settings.IS_PRODUCTION,
        "samesite": 'lax',
        "domain": settings.COOKIE_DOMAIN,
        "path": "/"
    }
    
    response.delete_cookie(key="access_token", **cookie_settings)
    response.delete_cookie(key="refresh_token", **cookie_settings)
    
    return {"message": "Successfully logged out"}