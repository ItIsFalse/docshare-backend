from sqlalchemy import Column, Integer, String, Boolean
from ..core.database import Base


class Region(Base):
    __tablename__ = "regions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(10), unique=True, nullable=False)
    is_active = Column(Boolean, default=True)