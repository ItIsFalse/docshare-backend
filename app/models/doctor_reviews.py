from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..core.database import Base


class DoctorReview(Base):
    __tablename__ = "doctor_reviews"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)

    rating = Column(Integer, nullable=False)  # 1-5
    description = Column(Text, nullable=True)

    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    doctor = relationship("Doctor", backref="reviews")
    patient = relationship("Patient", backref="reviews")
    appointment = relationship("Appointment", backref="reviews")