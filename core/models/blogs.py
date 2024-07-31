from sqlalchemy import Column, Boolean, Integer, String
from core.db import Base
from core.utils import enums


class Blogs(enums.BaseModelMixin, Base):
  """ default blogs models for Readre"""
  title = Column(String(30),unique=True)
  description = Column(String)
  
