from sqlalchemy import Column, String, Integer
from core.db import Base
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    picture = Column(String, nullable=True)
    refresh_token = Column(String, nullable=True)
    username = Column(String, unique=True, index=True)
    blogs = relationship("Blog", back_populates="user")
    comments = relationship("Comment", back_populates="user")
    likes = relationship("Like", back_populates="user")


     # Add this method to automatically generate a username if none is provided
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not kwargs.get('username') and 'email' in kwargs:
            # Generate username from email or name
            self.username = kwargs.get('name', '').replace(' ', '').lower() or \
                           kwargs['email'].split('@')[0]