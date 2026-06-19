from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from ..core.database import Base


class District(Base):
    __tablename__ = "districts"

    id = Column(Integer, primary_key=True, index=True)
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=False)

    name_uz = Column(String(100), nullable=False)
    name_ru = Column(String(100), nullable=False)
    name_en = Column(String(100), nullable=False)

    type = Column(String(50), default="district")  # district, city, etc.
    is_active = Column(Boolean, default=True)

    # Relationships
    region = relationship("Region", backref="districts")