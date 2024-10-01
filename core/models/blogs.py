from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from core.db import Base
from datetime import datetime
import math
from slugify import slugify

class Blog(Base):
    __tablename__ = "blogs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    slug = Column(String, unique=True, index=True)
    description = Column(Text)
    tag = Column(String)
    members_only = Column(Boolean, default=False)
    image = Column(String)
    date_added = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="blogs")
    comments = relationship("Comment", back_populates="blog")
    likes = relationship("Like", back_populates="blog", foreign_keys="[Like.blog_id]")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if 'title' in kwargs:
            self.slug = slugify(kwargs['title'])

    @property
    def word_count(self):
        return len(self.description.split())
      
    @property
    def reading_time(self):
        average_reading_speed = 200
        return math.ceil(self.word_count / average_reading_speed)

class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text)
    date_added = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))
    blog_id = Column(Integer, ForeignKey("blogs.id"))
    author = Column(String)
    user = relationship("User", back_populates="comments")
    blog = relationship("Blog", back_populates="comments")
    likes = relationship("Like", back_populates="comment")

class Like(Base):
    __tablename__ = "likes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    blog_id = Column(Integer, ForeignKey("blogs.id"), nullable=True)
    comment_id = Column(Integer, ForeignKey("comments.id"), nullable=True)

    user = relationship("User", back_populates="likes")
    blog = relationship("Blog", back_populates="likes", foreign_keys=[blog_id])
    comment = relationship("Comment", back_populates="likes")