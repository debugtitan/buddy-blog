from pydantic import BaseModel, HttpUrl, Field
from datetime import datetime
from core.utils import enums
from typing import Optional

class CommentBase(BaseModel):
    text: str

class CommentCreate(CommentBase):
    pass

class CommentUpdate(CommentBase):
    pass

class CommentRetrieve(BaseModel):
    id: int
    text: str
    date_added: datetime
    user_id: int
    blog_id: int
    author: str
    author_picture: Optional[str] =None
    liked: bool = False
    likes_count: int = 0

    class Config:
        from_attributes = True
class BlogRetrieve(BaseModel):
    id: int
    slug: str 
    date_added: datetime
    title: str
    description: str
    tag: str
    reading_time: int
    members_only: bool
    image: HttpUrl
    comments: list[CommentRetrieve] = []
    likes_count: int = 0

    class Config:
        from_attributes = True

class BlogCreate(BaseModel):
    title: str = Field(min_length=10, description="Blog title", max_length=60)
    description: str = Field(min_length=30, description="blog contents")
    tag: enums.BlogTagType = Field(
        default=enums.BlogTagType.EVENTS.value, description="Blog tag"
    )
    members_only: Optional[bool] = Field(
        default=False, description="Members only access"
    )
    image: str

    class Config:
        use_enum_values = True