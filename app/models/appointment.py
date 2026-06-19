from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..core.database import Base
import enum


class AppointmentStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"
    INCOMPLETE = "incomplete"


class AppointmentPriority(str, enum.Enum):
    NORMAL = "normal"
    URGENT = "urgent"
    CRITICAL = "critical"


class AppointmentType(str, enum.Enum):
    IN_PERSON = "in_person"
    VIDEO = "video"


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)

    scheduled_at = Column(DateTime, nullable=False)
    duration_min = Column(Integer, default=30)
    type = Column(String(20), default=AppointmentType.IN_PERSON.value)
    status = Column(String(20), default=AppointmentStatus.SCHEDULED.value)
    priority = Column(String(20), default=AppointmentPriority.NORMAL.value)

    reason = Column(Text, nullable=True)
    previous_appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    doctor = relationship("Doctor", backref="appointments")
    patient = relationship("Patient", backref="appointments")
    previous_appointment = relationship("Appointment", remote_side=[id], backref="rescheduled_to")