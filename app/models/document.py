from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Date, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..core.database import Base
import enum


class DocumentType(str, enum.Enum):
    REPORT = "report"
    PRESCRIPTION = "prescription"
    LAB_RESULT = "lab_result"
    IMAGING = "imaging"
    OTHER = "other"


class DocumentStatus(str, enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)

    title = Column(String(255), nullable=False)
    document_type = Column(String(50), default=DocumentType.OTHER.value)
    document_date = Column(Date, nullable=False)

    doctor_name = Column(String(100), nullable=True)
    hospital = Column(String(255), nullable=True)
    diagnosis = Column(Text, nullable=True)
    treatment = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    file_name = Column(String(255), nullable=True)
    file_url = Column(Text, nullable=True)
    file_size = Column(Integer, nullable=True)  # bytes

    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String(20), default=DocumentStatus.ACTIVE.value)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    patient = relationship("Patient", backref="documents")
    doctor = relationship("Doctor", backref="documents")
    appointment = relationship("Appointment", backref="documents")