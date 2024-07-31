from fastapi import APIRouter, status
from core.db import db_dependacy
from core.schemas.blogs import BlogRetrieve
from core.models.blogs import Blogs

blog_router = APIRouter(tags="Blog")

blog_router.get("/blog", status_code=status.HTTP_200_OK)


async def retrieve_blogs(db: db_dependacy) -> list[BlogRetrieve]:
    """"""
    blog_items = db.query(Blogs).all()
    print(blog_items)
