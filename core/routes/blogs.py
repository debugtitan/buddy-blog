from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from core.db import db_dependacy
from core.models.blogs import Blog, Comment, Like
from core.models.users import User
from core.schemas.blogs import BlogCreate, BlogRetrieve, CommentCreate, CommentRetrieve, CommentUpdate
from core.schemas.users import UserRetrieve
from typing import List
from core.routes.auth import get_current_user
from slugify import slugify


blog_router = APIRouter(tags=["Blogs"])

@blog_router.post("/blogs", response_model=BlogRetrieve)
async def create_blog(blog: BlogCreate, db: db_dependacy , current_user: User = Depends(get_current_user)):
    db_blog = Blog(**blog.dict(), user_id=current_user.id)
    db.add(db_blog)
    db.commit()
    db.refresh(db_blog)
    return db_blog

@blog_router.get("/blogs", response_model=List[BlogRetrieve])
async def get_blogs(db: db_dependacy):
    blogs = db.query(Blog).all()
    return blogs

@blog_router.get("/blogs/{slug}", response_model=BlogRetrieve)
async def get_blog(slug: str, db: db_dependacy):
    try:
        blog = db.query(Blog).filter(Blog.slug == slug).first()
        if blog is None:
            raise HTTPException(status_code=404, detail="Blog not found")
        
        comments = []
        for comment in blog.comments:
            author = db.query(User).filter(User.id == comment.user_id).first()
            
            comment_dict = CommentRetrieve(
                id=comment.id,
                text=comment.text,
                date_added=comment.date_added,
                user_id=comment.user_id,
                blog_id=comment.blog_id,
                author=comment.author,
                author_picture=author.picture,
                liked=False,  # This will be updated based on current user
                likes_count=db.query(Like).filter(Like.comment_id == comment.id).count()
            )
            comments.append(comment_dict)
        
        # Get likes for the blog post
        blog_likes_count = db.query(Like).filter(Like.blog_id == blog.id).count()
        
        return BlogRetrieve(
            id=blog.id,
            slug=blog.slug,
            date_added=blog.date_added,
            title=blog.title,
            description=blog.description,
            tag=blog.tag,
            reading_time=blog.reading_time,
            members_only=blog.members_only,
            image=blog.image,
            comments=comments,
            likes_count=blog_likes_count
        )
    except Exception as e:
        print(f"Error in get_blog: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    

@blog_router.get("/user/blogs", response_model=List[BlogRetrieve])
async def get_user_blogs(db: db_dependacy, current_user: User = Depends(get_current_user)):
    """Get all blogs created by the current user"""
    blogs = db.query(Blog).filter(Blog.user_id == current_user.id).all()
    return blogs

@blog_router.put("/blogs/{slug}", response_model=BlogRetrieve)
async def update_blog(
    slug: str, 
    blog_update: BlogCreate, 
    db: db_dependacy, 
    current_user: User = Depends(get_current_user)
):
    """Update a blog post"""
    blog = db.query(Blog).filter(Blog.slug == slug).first()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    
    if blog.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this blog")
    
    # Update blog fields
    for field, value in blog_update.dict().items():
        setattr(blog, field, value)
    
    # Update slug if title has changed
    if blog_update.title:
        blog.slug = slugify(blog_update.title)
    
    db.commit()
    db.refresh(blog)
    return blog

@blog_router.delete("/blogs/{slug}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_blog(
    slug: str, 
    db: db_dependacy, 
    current_user: User = Depends(get_current_user)
):
    """Delete a blog post"""
    blog = db.query(Blog).filter(Blog.slug == slug).first()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    
    if blog.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this blog")
    
    db.delete(blog)
    db.commit()
    return {"detail": "Blog deleted successfully"}

@blog_router.post("/blogs/{slug}/comments", response_model=CommentRetrieve)
async def create_comment(slug: str, comment: CommentCreate, db: db_dependacy, current_user: User = Depends(get_current_user)):
    try:
        blog = db.query(Blog).filter(Blog.slug == slug).first()
        if blog is None:
            raise HTTPException(status_code=404, detail="Blog not found")
        
        author_name = current_user.username or current_user.name
        
        db_comment = Comment(
            **comment.dict(),
            user_id=current_user.id,
            blog_id=blog.id,
            author=author_name 
        )
        db.add(db_comment)
        db.commit()
        db.refresh(db_comment)
        
        return CommentRetrieve(
            id=db_comment.id,
            text=db_comment.text,
            date_added=db_comment.date_added,
            user_id=db_comment.user_id,
            blog_id=db_comment.blog_id,
            author=author_name,
            author_picture=current_user.picture,
            liked=False,
            likes_count=0
        )
    except Exception as e:
        print(f"Error in create_comment: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@blog_router.get("/blogs/{slug}/comments", response_model=List[CommentRetrieve])
async def get_comments(slug: str, db: db_dependacy, current_user: User = Depends(get_current_user)):
    blog = db.query(Blog).filter(Blog.slug == slug).first()
    if blog is None:
        raise HTTPException(status_code=404, detail="Blog not found")
    
    comments = db.query(Comment).filter(Comment.blog_id == blog.id).all()
    
    comment_list = []
    for comment in comments:
        author = db.query(User).filter(User.id == comment.user_id).first()
        likes_count = db.query(Like).filter(Like.comment_id == comment.id).count()
        liked = db.query(Like).filter(Like.comment_id == comment.id, Like.user_id == current_user.id).first() is not None
        
        comment_data = CommentRetrieve(
            id=comment.id,
            text=comment.text,
            date_added=comment.date_added,
            user_id=comment.user_id,
            blog_id=comment.blog_id,
            author=author.username if author else "Unknown",
            author_picture=author.picture if author else "",
            liked=liked,
            likes_count=likes_count
        )
        comment_list.append(comment_data)
    
    return comment_list

@blog_router.put("/blogs/{slug}/comments/{comment_id}", response_model=CommentRetrieve)
async def update_comment(slug: str, comment_id: int, comment_update: CommentUpdate, db: db_dependacy, current_user: User = Depends(get_current_user)):
    blog = db.query(Blog).filter(Blog.slug == slug).first()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    
    comment = db.query(Comment).filter(Comment.id == comment_id, Comment.blog_id == blog.id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    if comment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this comment")
    
    comment.text = comment_update.text
    db.commit()
    db.refresh(comment)
    return comment

@blog_router.delete("/blogs/{slug}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(slug: str, comment_id: int, db: db_dependacy, current_user: User = Depends(get_current_user)):
    blog = db.query(Blog).filter(Blog.slug == slug).first()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    
    comment = db.query(Comment).filter(Comment.id == comment_id, Comment.blog_id == blog.id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    if comment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this comment")
    
    db.delete(comment)
    db.commit()
    return {"detail": "Comment deleted successfully"}


@blog_router.post("/blogs/{slug}/comments/{comment_id}/like", response_model=dict)
async def like_comment(
    slug: str, 
    comment_id: int, 
    db: db_dependacy, 
    current_user: User = Depends(get_current_user)
):
    try:
        # First, verify that the blog exists
        blog = db.query(Blog).filter(Blog.slug == slug).first()
        if not blog:
            raise HTTPException(status_code=404, detail="Blog not found")
        
        # Then, verify that the comment exists and belongs to this blog
        comment = db.query(Comment).filter(
            Comment.id == comment_id, 
            Comment.blog_id == blog.id
        ).first()
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")
        
        # Check if the user has already liked this comment
        existing_like = db.query(Like).filter(
            Like.user_id == current_user.id,
            Like.comment_id == comment_id
        ).first()
        
        if existing_like:
            # If like exists, remove it (unlike)
            db.delete(existing_like)
            db.commit()
            liked = False
        else:
            # If like doesn't exist, create it
            new_like = Like(
                user_id=current_user.id,
                comment_id=comment_id
            )
            db.add(new_like)
            db.commit()
            liked = True
        
        # Get updated like count
        likes_count = db.query(Like).filter(Like.comment_id == comment_id).count()
        
        return {
            "liked": liked,
            "likes_count": likes_count
        }
    
    except Exception as e:
        print(f"Error in like_comment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))



@blog_router.post("/blogs/{slug}/like", response_model=dict)
async def like_blog(slug: str, db: db_dependacy, current_user: User = Depends(get_current_user)):
    blog = db.query(Blog).filter(Blog.slug == slug).first()
    if blog is None:
        raise HTTPException(status_code=404, detail="Blog not found")
    
    like = db.query(Like).filter(Like.user_id == current_user.id, Like.blog_id == blog.id).first()
    if like:
        db.delete(like)
        db.commit()
        return {"liked": False, "likes_count": db.query(Like).filter(Like.blog_id == blog.id).count()}
    else:
        new_like = Like(user_id=current_user.id, blog_id=blog.id)
        db.add(new_like)
        db.commit()
        return {"liked": True, "likes_count": db.query(Like).filter(Like.blog_id == blog.id).count()}

@blog_router.get("/blogs/{slug}/like", response_model=dict)
async def get_like_status(slug: str, db: db_dependacy, current_user: User = Depends(get_current_user)):
    blog = db.query(Blog).filter(Blog.slug == slug).first()
    if blog is None:
        raise HTTPException(status_code=404, detail="Blog not found")
    
    like = db.query(Like).filter(Like.user_id == current_user.id, Like.blog_id == blog.id).first()
    likes_count = db.query(Like).filter(Like.blog_id == blog.id).count()
    return {"liked": like is not None, "likes_count": likes_count}