from sqlalchemy import Column, Boolean, Integer, String
from core.db import Base
from core.utils import enums


class Blogs(enums.BaseModelMixin, Base):
  """ default blogs models for buddy-blog"""
