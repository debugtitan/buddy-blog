from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime
from core.utils import enums


class BlogRetrieve(BaseModel):
    id: int
    date_added: datetime
    date_last_updated: datetime
    title: str
    description: str
    tag: str
    reading_time: int
    members_only: bool

    class Config:
        from_attributes = True


class BlogCreate(BaseModel):
    title: str = Field(min_length=10, description="Blog title", max_length=30)
    description: str = Field(min_length=30, description="blog contents")
    tag: enums.BlogTagType = Field(
        default=enums.BlogTagType.values(), description="Blog tag"
    )
    members_only: Optional[bool] = Field(
        default=False, description="Members only access"
    )

    class Config:
        use_enum_values = True
