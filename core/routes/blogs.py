from fastapi import APIRouter, status
from core.db import db_dependacy
from core.schemas.blogs import BlogRetrieve
from core.models.blogs import Blogs

blog_router = APIRouter(tags=["Blogs"])


@blog_router.get("/blogs", status_code=status.HTTP_200_OK)
async def retrieve_blogs(db: db_dependacy) -> list[BlogRetrieve]:
    blog_items = db.query(Blogs).all()
    return [BlogRetrieve.model_validate(blog) for blog in blog_items]
