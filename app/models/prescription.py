from sqlalchemy import Column, Integer, String, DateTime, Date, Text, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..core.database import Base
import enum


class PrescriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class Prescription(Base):
    __tablename__ = "prescriptions"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)

    medication_name = Column(String(255), nullable=False)
    dosage = Column(String(100), nullable=False)
    dosage_form = Column(String(100), nullable=False)
    frequency = Column(String(100), nullable=False)
    time_of_day = Column(String(100), nullable=True)

    duration_days = Column(Integer, nullable=True)
    quantity = Column(Integer, nullable=True)
    left_quantity = Column(Integer, nullable=True)

    status = Column(String(20), default=PrescriptionStatus.ACTIVE.value)
    prescribed_at = Column(Date, server_default=func.current_date())
    expires_at = Column(Date, nullable=True)

    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    patient = relationship("Patient", backref="prescriptions")
    doctor = relationship("Doctor", backref="prescriptions")
    appointment = relationship("Appointment", backref="prescriptions")