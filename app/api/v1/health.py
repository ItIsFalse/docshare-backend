from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.patient import Patient
from app.models.medical_record import MedicalRecord

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/medical-history")
def get_medical_history(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Получить историю болезни"""
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    if not patient:
        return []

    records = db.query(MedicalRecord).filter(
        MedicalRecord.patient_id == patient.id
    ).order_by(MedicalRecord.record_date.desc()).all()

    return [
        {
            "id": r.id,
            "title": r.diagnosis or r.record_type,
            "diagnosis": r.diagnosis,
            "treatment": r.treatment,
            "status": r.outcome or "ongoing",
            "record_date": r.record_date.strftime("%Y-%m-%d") if r.record_date else None,
            "doctor_name": "Dr. Karimov",  # TODO: взять из doctor
            "severity": r.severity
        }
        for r in records
    ]


@router.get("/current-status")
def get_current_health_status(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Получить текущий статус здоровья"""
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    if not patient:
        return {
            "overall_score": 8.5,
            "risk_factors": ["No data available"],
            "active_conditions": [],
            "vaccinations": "Up to date"
        }

    # Получаем активные записи
    active_records = db.query(MedicalRecord).filter(
        MedicalRecord.patient_id == patient.id,
        MedicalRecord.outcome.in_(["ongoing", "improving", "managing"])
    ).all()

    return {
        "overall_score": 8.5,
        "risk_factors": ["Air pollution", "Sleep deprivation"],
        "active_conditions": [r.diagnosis for r in active_records if r.diagnosis],
        "vaccinations": "Up to date"
    }