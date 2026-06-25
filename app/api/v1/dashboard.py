from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.patient import Patient
from app.models.activity import Activity
from app.models.appointment import Appointment
from app.models.family_member import FamilyMember
from app.models.health_metric import HealthMetric

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def get_patient_id(user_id: int, db: Session) -> int:
    patient = db.query(Patient).filter(Patient.user_id == user_id).first()
    if not patient:
        patient = Patient(user_id=user_id)
        db.add(patient)
        db.commit()
        db.refresh(patient)
    return patient.id


def get_vitals_summary(db: Session, patient_id: int):
    """Получить витальные показатели для дашборда"""
    metrics = {}
    types = ["heart_rate", "blood_pressure_systolic", "spo2", "weight"]

    for mt in types:
        metric = db.query(HealthMetric).filter(
            HealthMetric.patient_id == patient_id,
            HealthMetric.metric_type == mt
        ).order_by(HealthMetric.measured_at.desc()).first()

        if metric:
            metrics[mt] = metric.value

    cards = []

    # Heart Rate
    if "heart_rate" in metrics:
        cards.append({
            "key": "heart_rate",
            "label": "Heart Rate",
            "value": metrics["heart_rate"],
            "unit": "BPM",
            "trend_percent": 5.9,
            "trend_direction": "up",
            "in_range": True,
            "secondary_value": None
        })

    # Blood Pressure
    if "blood_pressure_systolic" in metrics:
        cards.append({
            "key": "blood_pressure",
            "label": "Blood Pressure",
            "value": metrics["blood_pressure_systolic"],
            "unit": "mmHg",
            "trend_percent": 1.7,
            "trend_direction": "up",
            "in_range": True,
            "secondary_value": 80
        })

    # SpO2
    if "spo2" in metrics:
        cards.append({
            "key": "spo2",
            "label": "SpO2",
            "value": metrics["spo2"],
            "unit": "%",
            "trend_percent": 1.0,
            "trend_direction": "down",
            "in_range": True,
            "secondary_value": None
        })

    # Weight
    if "weight" in metrics:
        cards.append({
            "key": "weight",
            "label": "Weight",
            "value": metrics["weight"],
            "unit": "kg",
            "trend_percent": 0.3,
            "trend_direction": "up",
            "in_range": True,
            "secondary_value": None
        })

    # Если нет данных — возвращаем заглушки
    if not cards:
        cards = [
            {"key": "heart_rate", "label": "Heart Rate", "value": 72, "unit": "BPM", "trend_percent": 5.9,
             "trend_direction": "up", "in_range": True, "secondary_value": None},
            {"key": "blood_pressure", "label": "Blood Pressure", "value": 120, "unit": "mmHg", "trend_percent": 1.7,
             "trend_direction": "up", "in_range": True, "secondary_value": 80},
            {"key": "spo2", "label": "SpO2", "value": 98, "unit": "%", "trend_percent": 1.0, "trend_direction": "down",
             "in_range": True, "secondary_value": None},
            {"key": "weight", "label": "Weight", "value": 78.5, "unit": "kg", "trend_percent": 0.3,
             "trend_direction": "up", "in_range": True, "secondary_value": None}
        ]

    return {"cards": cards}


def get_family_summary(db: Session, patient_id: int):
    """Получить семейную статистику"""
    members = db.query(FamilyMember).filter(
        FamilyMember.patient_id == patient_id,
        FamilyMember.status == "active"
    ).all()

    total = len(members)
    good = sum(1 for m in members if m.health_status == "good")
    attention = sum(1 for m in members if m.health_status == "attention")
    critical = sum(1 for m in members if m.health_status == "critical")
    avg_score = sum(m.health_score or 80 for m in members) // total if total > 0 else 0

    return {
        "average_score": avg_score,
        "members_good": good,
        "members_attention": attention,
        "members_critical": critical,
        "total_members": total
    }


@router.get("/")
def get_dashboard(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Комбинированный дашборд для фронтенда"""
    patient_id = get_patient_id(current_user.id, db)

    # Пользователь
    user_data = {
        "full_name": current_user.full_name,
        "health_score": 85
    }

    # Vitals
    vitals = get_vitals_summary(db, patient_id)

    # Активности на сегодня
    today = datetime.now().replace(hour=0, minute=0, second=0)
    activities = db.query(Activity).filter(
        Activity.patient_id == patient_id,
        Activity.activity_date >= today
    ).limit(4).all()

    # Следующая запись
    next_appointment = db.query(Appointment).filter(
        Appointment.patient_id == patient_id,
        Appointment.status == "scheduled",
        Appointment.scheduled_at >= datetime.now()
    ).order_by(Appointment.scheduled_at).first()

    # Семья
    family_summary = get_family_summary(db, patient_id)

    return {
        "user": user_data,
        "vitals_summary": vitals,
        "activities": [
            {
                "id": a.id,
                "title": a.title,
                "description": a.description,
                "category": a.category,
                "duration_minutes": a.duration_minutes,
                "completed": a.completed,
                "streak": a.streak,
                "activity_date": a.activity_date
            }
            for a in activities
        ],
        "next_appointment": {
            "doctor_name": "Dr. John Doe",
            "date": next_appointment.scheduled_at.strftime("%Y-%m-%d") if next_appointment else None,
            "time": next_appointment.scheduled_at.strftime("%H:%M") if next_appointment else None,
            "status": next_appointment.status if next_appointment else None
        } if next_appointment else None,
        "family_summary": family_summary
    }