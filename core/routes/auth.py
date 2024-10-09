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
from typing import Optional
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

def get_current_user(
    db: db_dependacy,
    access_token: Optional[str]  = Cookie(None),
    refresh_token: Optional[str] = Cookie(None)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not access_token and not refresh_token:
        raise credentials_exception
    
    try:
        if access_token:
            # Try to decode the access token
            payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
            user_email = payload.get("sub")
            if user_email is None:
                raise credentials_exception
        elif refresh_token:
            # If no access token but refresh token exists, try to find user by refresh token
            user = db.query(User).filter(User.refresh_token == refresh_token).first()
            if not user:
                raise credentials_exception
            user_email = user.email
        else:
            raise credentials_exception
        
        # Fetch the user from the database
        user = db.query(User).filter(User.email == user_email).first()
        if user is None:
            raise credentials_exception
        return user
    except JWTError:
        raise credentials_exception

@auth_router.get("/auth/me", response_model=UserRetrieve)
async def get_current_user_info(
    response: Response,
    current_user: User = Depends(get_current_user),
    db: db_dependacy = db_dependacy,
):
    
    # Create a new access token
    access_token = create_access_token({"sub": current_user.email})
    
    # Set the access token in a cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,  # Use this in production with HTTPS
        samesite='lax',
        max_age=60 * ACCESS_TOKEN_EXPIRE_MINUTES,
        path="/"
    )
    
    return current_user

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
        # Log the beginning of the authentication process
        print(f"Starting Google authentication process")
        
        # Fetch user info from Google
        google_response = requests.get(
            f'https://www.googleapis.com/oauth2/v3/userinfo',
            params={'access_token': token_data.token},
            timeout=5  # 5 seconds timeout
        )
        
        # Check if the Google API request was successful
        if google_response.status_code != 200:
            print(f"Google API error: {google_response.status_code} - {google_response.text}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Failed to verify Google token: {google_response.status_code}"
            )
        
        # Parse the user data from Google
        user_data = google_response.json()
        print(f"Received user data from Google: {user_data}")
        
        # Extract required user information
        user_email = user_data.get('email')
        if not user_email:
            raise ValueError("Email not provided by Google")
        
        user_name = user_data.get('name', '')
        user_picture = user_data.get('picture', '')

        # Find or create user in database
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
        
        # Create tokens
        access_token = create_access_token({"sub": user_email})
        refresh_token = create_refresh_token()
        
        # Update user's refresh token in database
        user.refresh_token = refresh_token
        db.commit()
        db.refresh(user)

        # Set access token cookie
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,  # Set to True in production
            samesite='lax',
            max_age=60 * ACCESS_TOKEN_EXPIRE_MINUTES,  # Use your constant here
            path="/"
        )
        
        # Set refresh token cookie
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,  # Set to True in production
            samesite='lax',
            max_age=60 * 60 * 24 * REFRESH_TOKEN_EXPIRE_DAYS,  # Use your constant here
            path="/"
        )

        print(f"Authentication successful for user: {user_email}")
        
        # Return the response
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": UserRetrieve.model_validate(user)
        }

    except requests.RequestException as e:
        print(f"Network error during Google authentication: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to connect to Google: {str(e)}"
        )
    except ValueError as e:
        print(f"Validation error during authentication: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        print(f"Unexpected error during authentication: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
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
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/")
    return {"message": "Successfully logged out"}


