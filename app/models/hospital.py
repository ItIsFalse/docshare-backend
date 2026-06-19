from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..core.database import Base


class Hospital(Base):
    __tablename__ = "hospitals"

    id = Column(Integer, primary_key=True, index=True)
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=False)
    district_id = Column(Integer, ForeignKey("districts.id"), nullable=True)

    name_uz = Column(String(255), nullable=False)
    name_ru = Column(String(255), nullable=False)
    name_en = Column(String(255), nullable=False)

    facility_type = Column(String(50), nullable=True)  # polyclinic, hospital, diagnostic_center, etc.
    description = Column(Text, nullable=True)

    doctor_count = Column(Integer, default=0)
    has_icu = Column(Boolean, default=False)
    rating = Column(Float, default=0.0)

    full_address = Column(Text, nullable=True)
    longitude = Column(Float, nullable=True)
    latitude = Column(Float, nullable=True)

    has_emergency_home_visit = Column(Boolean, default=False)
    registration_phone = Column(String(50), nullable=True)
    website = Column(String(255), nullable=True)
    parking_spots = Column(Integer, nullable=True)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    region = relationship("Region", backref="hospitals")
    district = relationship("District", backref="hospitals")