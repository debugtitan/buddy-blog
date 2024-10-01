from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    name: str

class UserRetrieve(BaseModel):
    id: int
    email: str
    name: str
    picture: str | None

    class Config:
        from_attributes = True