from enum import Enum
from sqlalchemy import Column, Integer, DateTime, func
from sqlalchemy.ext.declarative import declared_attr


class BaseModelMixin:
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    id = Column(Integer, primary_key=True, index=True)
    date_added = Column(DateTime, default=func.now())
    date_last_updated = Column(DateTime, default=func.now(), onupdate=func.now())

    def __str__(self):
        return f"< {type(self).__name__}({self.id}) >"


class BaseEnum(Enum):
    @classmethod
    def choices(cls):
        return [(i.value, i.name) for i in cls]

    @classmethod
    def values(cls):
        return list(i.value for i in cls)

    @classmethod
    def count(cls):
        return len(cls)

    @classmethod
    def mapping(cls):
        return dict((i.name, i.value) for i in cls)
