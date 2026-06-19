from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from ..core.database import Base


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=False)

    specialization = Column(String(100), nullable=False)
    license_number = Column(String(50), unique=True, nullable=False)
    license_status = Column(String(20), default="active")  # active, expired, suspended
    years_of_experience = Column(Integer, default=0)
    rating = Column(Float, default=0.0)
    is_accepting_patients = Column(Boolean, default=True)

    # Relationships
    user = relationship("User", backref="doctor_profile", uselist=False)
    region = relationship("Region")