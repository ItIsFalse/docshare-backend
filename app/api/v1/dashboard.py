from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_citizen
from app.models.user import User
from app.models.patient import Patient
from app.models.health_metric import HealthMetric
from app.models.appointment import Appointment
from app.models.family_member import FamilyMember
from app.models.doctor import Doctor

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/")
def get_dashboard(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Главный экран пользователя (Dashboard)
    Собирает все данные в один ответ для фронтенда
    """

    # Получаем пациента
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    if not patient:
        # Если пациент не найден, создаем базового
        patient = Patient(user_id=current_user.id)
        db.add(patient)
        db.commit()
        db.refresh(patient)

    # 1. Получаем последние витальные показатели
    latest_vitals = db.query(HealthMetric).filter(
        HealthMetric.patient_id == patient.id
    ).order_by(HealthMetric.measured_at.desc()).limit(4).all()

    vitals_cards = []
    for metric in latest_vitals:
        vitals_cards.append({
            "key": metric.metric_type,
            "label": _get_metric_label(metric.metric_type),
            "value": metric.value,
            "unit": metric.unit,
            "in_range": True,  # TODO: добавить проверку нормы
            "trend_percent": 0,  # TODO: рассчитать тренд
            "trend_direction": "up"
        })

    # Если нет данных, показываем заглушки
    if not vitals_cards:
        vitals_cards = [
            {"key": "hr_bpm", "label": "Heart Rate", "value": 72, "unit": "BPM", "in_range": True, "trend_percent": 0,
             "trend_direction": "up"},
            {"key": "bp_sys", "label": "Blood Pressure", "value": 120, "unit": "mmHg", "in_range": True,
             "trend_percent": 0, "trend_direction": "up"},
            {"key": "spo2", "label": "SpO2", "value": 98, "unit": "%", "in_range": True, "trend_percent": 0,
             "trend_direction": "down"},
            {"key": "steps", "label": "Steps Today", "value": 8450, "unit": "steps", "in_range": True,
             "trend_percent": 0, "trend_direction": "down"}
        ]

    # 2. Получаем предстоящие записи (макс 3)
    upcoming_appointments = db.query(Appointment).filter(
        Appointment.patient_id == patient.id,
        Appointment.status == "scheduled",
        Appointment.scheduled_at >= datetime.now()
    ).order_by(Appointment.scheduled_at).limit(3).all()

    appointments_data = []
    for apt in upcoming_appointments:
        doctor = db.query(Doctor).filter(Doctor.id == apt.doctor_id).first()
        appointments_data.append({
            "id": apt.id,
            "doctor_id": apt.doctor_id,
            "doctor_name": doctor.user.full_name if doctor else "Dr. Unknown",
            "specialty": doctor.specialization if doctor else "Unknown",
            "hospital": "Tashkent Medical Center",  # TODO: добавить hospital_id
            "date": apt.scheduled_at.strftime("%Y-%m-%d"),
            "time": apt.scheduled_at.strftime("%H:%M"),
            "status": apt.status
        })

    # 3. Получаем членов семьи
    family_members = db.query(FamilyMember).filter(
        FamilyMember.patient_id == patient.id,
        FamilyMember.status == "active"
    ).all()

    family_data = []
    for member in family_members:
        # Определяем статус здоровья (заглушка)
        health_status = "good"  # good | attention | critical
        family_data.append({
            "id": member.id,
            "name": member.info.split(",")[0] if member.info else "Unknown",
            "relation": member.relationship_type,
            "health_status": health_status
        })

    # 4. Ежедневная активность (заглушка)
    daily_activity = {
        "steps": 8450,
        "steps_goal": 10000,
        "calories": 450,
        "distance_km": 6.2,
        "day_streak": 5,
        "weekly_trend": [60, 80, 45, 90, 70, 85, 100],
        "weekly_change_percent": 12
    }

    # 5. Ежедневные цели (заглушка)
    daily_goals = [
        {"id": "goal_1", "title": "Morning Walk", "description": "30 minutes of brisk walking", "completed": True},
        {"id": "goal_2", "title": "Meditation", "description": "10 minutes of breathing exercises", "completed": True},
        {"id": "goal_3", "title": "8 Hours Sleep", "description": "Maintain consistent sleep schedule",
         "completed": False},
        {"id": "goal_4", "title": "Drink 2L Water", "description": "Stay hydrated throughout the day",
         "completed": False}
    ]

    # 6. AI Tips (заглушка)
    ai_tips = [
        {"id": "tip_1", "title": "Stay Hydrated", "description": "You've only had 1.2L today. Aim for 2L.",
         "type": "tip"},
        {"id": "tip_2", "title": "Blood Pressure Check",
         "description": "Your BP is slightly elevated. Consider reducing salt.", "type": "warning"},
        {"id": "tip_3", "title": "Sleep Schedule", "description": "Great job maintaining your 8-hour sleep schedule!",
         "type": "tip"}
    ]

    # 7. Hero stats
    hero_stats = {
        "hr_bpm": 72,
        "aqi": 42,
        "aqi_level": "Good",
        "steps": 8450
    }

    # 8. Семейная оценка здоровья (заглушка)
    family_health_score = 87

    return {
        "user": {
            "full_name": current_user.full_name,
            "health_score": 85  # TODO: рассчитать реальный score
        },
        "daily_activity": daily_activity,
        "vitals": vitals_cards,
        "daily_goals": daily_goals,
        "appointments": appointments_data,
        "family": family_data,
        "family_health_score": family_health_score,
        "ai_tips": ai_tips,
        "hero_stats": hero_stats
    }


def _get_metric_label(metric_type: str) -> str:
    """Возвращает человеческое название метрики"""
    labels = {
        "heart_rate": "Heart Rate",
        "blood_pressure_systolic": "Blood Pressure",
        "spo2": "SpO2",
        "steps": "Steps Today",
        "weight": "Weight",
        "blood_glucose": "Glucose",
        "temperature": "Temperature"
    }
    return labels.get(metric_type, metric_type)