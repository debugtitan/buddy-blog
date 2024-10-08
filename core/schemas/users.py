from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    email: EmailStr
    name: str

class UserRetrieve(BaseModel):
    id: int
    email: str
    name: str
    picture: Optional[str] = None 

    class Config:
        from_attributes = True