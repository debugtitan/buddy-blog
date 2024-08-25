from fastapi import APIRouter, status, HTTPException, UploadFile, File
from core.db import db_dependacy
from core.schemas.blogs import BlogRetrieve, BlogCreate
from core.models.blogs import Blogs
from slugify import slugify


blog_router = APIRouter(tags=["Blogs"])

@blog_router.post("/blogs", status_code=status.HTTP_201_CREATED)
async def create_new_blog(db: db_dependacy, blog_data: BlogCreate) -> BlogRetrieve:
    slug = slugify(blog_data.title)
    
    if not slug:
        raise HTTPException(status_code=400, detail="Invalid slug generated")

    existing_blog = db.query(Blogs).filter(Blogs.slug == slug).first()
    if existing_blog:
        raise HTTPException(status_code=400, detail="Slug already exists")

    

    new_blog = Blogs(
        title=blog_data.title,
        slug=slug,
        description=blog_data.description,
        tag=blog_data.tag,
        members_only=blog_data.members_only,
    )

    try:
        db.add(new_blog)
        db.commit()
        db.refresh(new_blog)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database operation failed")

    return BlogRetrieve.model_validate(new_blog)


@blog_router.get("/blogs", status_code=status.HTTP_200_OK)
async def get_all_blogs(db: db_dependacy) -> list[BlogRetrieve]:
    blogs = db.query(Blogs).all()
    return [BlogRetrieve.model_validate(blog) for blog in blogs]



@blog_router.get("/blogs/{slug}", status_code=status.HTTP_200_OK)
async def get_blog(db: db_dependacy, slug: str) -> BlogRetrieve:
    blog_model = db.query(Blogs).filter(Blogs.slug == slug).first()
    if blog_model is None:
        raise HTTPException(status_code=404, detail="Blog not found")

    return BlogRetrieve.model_validate(blog_model)
