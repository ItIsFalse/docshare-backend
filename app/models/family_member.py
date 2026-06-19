from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Date
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..core.database import Base


class FamilyMember(Base):
    __tablename__ = "family_members"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    relative_patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True)

    has_account = Column(Boolean, default=False)

    # ИЗМЕНЕНО: String(500) вместо String(100)
    name = Column(String(500), nullable=True)
    info = Column(Text, nullable=True)
    relationship_type = Column(String(50), default="other")
    status = Column(String(20), default="active")

    date_of_birth = Column(Date, nullable=True)
    gender = Column(String(20), nullable=True)
    blood_type = Column(String(10), nullable=True)
    allergies = Column(Text, nullable=True)
    chronic_conditions = Column(Text, nullable=True)
    health_status = Column(String(20), default="good")
    health_score = Column(Integer, default=80)
    last_checkup = Column(Date, nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    patient = relationship("Patient", foreign_keys=[patient_id], backref="family_members")
    relative = relationship("Patient", foreign_keys=[relative_patient_id], backref="related_family_members")