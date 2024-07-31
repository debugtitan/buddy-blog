from pydantic import BaseModel
from datetime import datetime


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
