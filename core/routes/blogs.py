from fastapi import APIRouter, status
from core.db import db_dependacy
from core.schemas.blogs import BlogRetrieve, BlogCreate
from core.models.blogs import Blogs

blog_router = APIRouter(tags=["Blogs"])


@blog_router.get("/blogs", status_code=status.HTTP_200_OK)
async def retrieve_blogs(db: db_dependacy) -> list[BlogRetrieve]:
    blog_items = db.query(Blogs).all()
    return [BlogRetrieve.model_validate(blog) for blog in blog_items]


@blog_router.post("/blogs", status_code=status.HTTP_201_CREATED)
async def create_new_blog(db: db_dependacy, blog_data: BlogCreate):
    new_blog = Blogs(
        title=blog_data.title,
        description=blog_data.description,
        tag=blog_data.tag,
        members_only=blog_data.members_only,
    )
    db.add(new_blog)
    db.commit()
    db.refresh(new_blog)
    return new_blog
