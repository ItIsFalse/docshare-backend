from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey
from sqlalchemy.orm import relationship
from ..core.database import Base


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    region_id = Column(Integer, ForeignKey("regions.id"), nullable=True)

    blood_type = Column(String(10), nullable=True)
    allergies = Column(Text, nullable=True)
    chronic_diseases = Column(Text, nullable=True)
    emergency_contact_name = Column(String(100), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)

    date_of_birth = Column(Date, nullable=True)
    gender = Column(String(20), nullable=True)  # male, female, other

    # Relationships
    user = relationship("User", backref="patient_profile", uselist=False)
    region = relationship("Region")