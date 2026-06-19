from sqlalchemy import Column, Integer, String, DateTime, Float, Text, ForeignKey, BigInteger
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..core.database import Base


class HealthMetric(Base):
    __tablename__ = "health_metrics"

    id = Column(BigInteger, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)

    metric_type = Column(String(50), nullable=False)  # heart_rate, blood_pressure_systolic, steps, etc.
    value = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)

    measured_at = Column(DateTime, nullable=False)
    source = Column(String(50), default="manual")  # watch, manual, external
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    patient = relationship("Patient", backref="health_metrics")