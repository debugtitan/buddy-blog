import math
from sqlalchemy import Column, Boolean, String, Enum
from core.db import Base
from core.utils import enums


class Blogs(enums.BaseModelMixin, Base):
    """default blogs models for Readre"""

    title = Column(String(30), unique=True)
    description = Column(String)
    tag = Column(Enum(enums.BlogTagType), default=enums.BlogTagType.EVENTS.value)
    members_only = Column(Boolean, default=False)

    @property
    def word_count(self):
        """count total blog content words"""
        return len(self.description.split())
      
    @property
    def reading_time(self):
        """ Average reading speed in words per minute """
        average_reading_speed = 200
        return math.ceil(self.word_count / average_reading_speed)
