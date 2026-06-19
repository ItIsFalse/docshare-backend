from sqlalchemy import Column, Integer, String, DateTime, Date, Text, Boolean, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..core.database import Base
import enum


class RecordType(str, enum.Enum):
    DIAGNOSIS = "diagnosis"
    PROCEDURE = "procedure"
    LAB_RESULT = "lab_result"
    VACCINATION = "vaccination"
    PRESCRIPTION = "prescription"
    SURGERY = "surgery"
    DISCHARGE_SUMMARY = "discharge_summary"


class VisitType(str, enum.Enum):
    INITIAL = "initial"
    FOLLOW_UP = "follow_up"
    EMERGENCY = "emergency"
    CONSULTATION = "consultation"
    INPATIENT = "inpatient"


class RecordStatus(str, enum.Enum):
    PRELIMINARY = "preliminary"
    FINAL = "final"
    AMENDED = "amended"
    CANCELLED = "cancelled"


class Severity(str, enum.Enum):
    MILD = "mild"
    MEDIUM = "medium"
    SEVERE = "severe"
    CRITICAL = "critical"


class MedicalRecord(Base):
    __tablename__ = "medical_records"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)

    record_type = Column(String(50), nullable=False)
    visit_type = Column(String(50), default=VisitType.CONSULTATION.value)
    icd10_code = Column(String(20), nullable=True)

    diagnosis = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    treatment = Column(Text, nullable=True)
    medications = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    status = Column(String(20), default=RecordStatus.FINAL.value)
    severity = Column(String(20), default=Severity.MEDIUM.value)
    outcome = Column(String(50), nullable=True)  # recovered, improved, stable, referred, deceased

    record_date = Column(Date, server_default=func.current_date())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    verified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    verified_at = Column(DateTime, nullable=True)

    parent_record_id = Column(Integer, ForeignKey("medical_records.id"), nullable=True)
    is_confidential = Column(Boolean, default=False)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    patient = relationship("Patient", backref="medical_records")
    doctor = relationship("Doctor", backref="medical_records")
    appointment = relationship("Appointment", backref="medical_records")
    creator = relationship("User", foreign_keys=[created_by])
    verifier = relationship("User", foreign_keys=[verified_by])
    parent_record = relationship("MedicalRecord", remote_side=[id], backref="children")