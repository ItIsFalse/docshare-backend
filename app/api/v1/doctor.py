from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
from typing import Optional, List
import random

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_doctor
from app.models.user import User
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.appointment import Appointment
from app.models.doctor_reviews import DoctorReview
from app.models.region import Region
from app.schemas.doctor import (
    DoctorScheduleItem, DoctorRequestItem, DoctorStatsResponse,
    DoctorRatingResponse, DoctorReviewResponse, DoctorHistoryItem
)

router = APIRouter(prefix="/doctor", tags=["Doctor"])


def get_doctor_id(user_id: int, db: Session) -> int:
    """Получает doctor_id по user_id"""
    doctor = db.query(Doctor).filter(Doctor.user_id == user_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor profile not found")
    return doctor.id


@router.get("/schedule", response_model=List[DoctorScheduleItem])
def get_doctor_schedule(
        date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
        db: Session = Depends(get_db),
        current_user: User = Depends(require_doctor)
):
    """Получить расписание врача на день"""
    doctor_id = get_doctor_id(current_user.id, db)

    if date:
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format")
    else:
        target_date = datetime.now()

    start_date = target_date.replace(hour=0, minute=0, second=0)
    end_date = target_date.replace(hour=23, minute=59, second=59)

    appointments = db.query(Appointment).filter(
        Appointment.doctor_id == doctor_id,
        Appointment.scheduled_at >= start_date,
        Appointment.scheduled_at <= end_date,
        Appointment.status.in_(["scheduled", "completed"])
    ).order_by(Appointment.scheduled_at).all()

    result = []
    for apt in appointments:
        patient = db.query(Patient).filter(Patient.id == apt.patient_id).first()
        patient_user = db.query(User).filter(User.id == patient.user_id).first() if patient else None

        result.append(DoctorScheduleItem(
            id=apt.id,
            patient_name=patient_user.full_name if patient_user else "Unknown",
            time=apt.scheduled_at.strftime("%H:%M"),
            type=apt.type or "in_person",
            reason=apt.reason,
            status=apt.status
        ))

    return result


@router.get("/requests", response_model=List[DoctorRequestItem])
def get_doctor_requests(
        db: Session = Depends(get_db),
        current_user: User = Depends(require_doctor)
):
    """Получить ожидающие запросы от пациентов"""
    doctor_id = get_doctor_id(current_user.id, db)

    # Получаем предстоящие appointments с статусом scheduled
    appointments = db.query(Appointment).filter(
        Appointment.doctor_id == doctor_id,
        Appointment.status == "scheduled",
        Appointment.scheduled_at >= datetime.now()
    ).order_by(Appointment.scheduled_at).limit(10).all()

    result = []
    for apt in appointments:
        patient = db.query(Patient).filter(Patient.id == apt.patient_id).first()
        patient_user = db.query(User).filter(User.id == patient.user_id).first() if patient else None

        # Вычисляем возраст
        age = 30
        if patient and patient.date_of_birth:
            age = datetime.now().year - patient.date_of_birth.year

        # Время создания (заглушка)
        created_ago = random.choice(["2 hours ago", "5 hours ago", "1 day ago"])

        result.append(DoctorRequestItem(
            id=apt.id,
            patient_name=patient_user.full_name if patient_user else "Unknown",
            age=age,
            reason=apt.reason or "General consultation",
            date=apt.scheduled_at.strftime("%Y-%m-%d"),
            time=apt.scheduled_at.strftime("%H:%M"),
            created_at=created_ago
        ))

    return result


@router.post("/requests/{request_id}/accept")
def accept_request(
        request_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_doctor)
):
    """Принять запрос пациента"""
    doctor_id = get_doctor_id(current_user.id, db)

    appointment = db.query(Appointment).filter(
        Appointment.id == request_id,
        Appointment.doctor_id == doctor_id
    ).first()

    if not appointment:
        raise HTTPException(status_code=404, detail="Request not found")

    appointment.status = "scheduled"
    db.commit()

    return {"success": True, "message": "Request accepted"}


@router.post("/requests/{request_id}/reject")
def reject_request(
        request_id: int,
        reason: Optional[str] = None,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_doctor)
):
    """Отклонить запрос пациента"""
    doctor_id = get_doctor_id(current_user.id, db)

    appointment = db.query(Appointment).filter(
        Appointment.id == request_id,
        Appointment.doctor_id == doctor_id
    ).first()

    if not appointment:
        raise HTTPException(status_code=404, detail="Request not found")

    appointment.status = "cancelled"
    db.commit()

    return {"success": True, "message": "Request rejected"}


@router.get("/stats", response_model=DoctorStatsResponse)
def get_doctor_stats(
        db: Session = Depends(get_db),
        current_user: User = Depends(require_doctor)
):
    """Получить статистику врача"""
    doctor_id = get_doctor_id(current_user.id, db)

    # Сегодняшние пациенты
    today = datetime.now().replace(hour=0, minute=0, second=0)
    tomorrow = today + timedelta(days=1)

    patients_today = db.query(Appointment).filter(
        Appointment.doctor_id == doctor_id,
        Appointment.scheduled_at >= today,
        Appointment.scheduled_at < tomorrow,
        Appointment.status == "scheduled"
    ).count()

    # Консультации за неделю
    week_ago = datetime.now() - timedelta(days=7)
    consultations_week = db.query(Appointment).filter(
        Appointment.doctor_id == doctor_id,
        Appointment.scheduled_at >= week_ago,
        Appointment.status == "completed"
    ).count()

    # Всего пациентов
    total_patients = db.query(Appointment).filter(
        Appointment.doctor_id == doctor_id
    ).distinct(Appointment.patient_id).count()

    # Рейтинг
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    rating = doctor.rating or 4.9

    # Ожидающие запросы
    pending_requests = db.query(Appointment).filter(
        Appointment.doctor_id == doctor_id,
        Appointment.status == "scheduled",
        Appointment.scheduled_at >= datetime.now()
    ).count()

    # Рост (заглушка)
    growth_percent = 12.0

    return DoctorStatsResponse(
        patients_today=patients_today,
        consultations_week=consultations_week,
        rating=rating,
        pending_requests=pending_requests,
        total_patients=total_patients,
        growth_percent=growth_percent
    )


@router.get("/ratings", response_model=DoctorRatingResponse)
def get_doctor_ratings(
        db: Session = Depends(get_db),
        current_user: User = Depends(require_doctor)
):
    """Получить рейтинг и отзывы врача"""
    doctor_id = get_doctor_id(current_user.id, db)

    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    rating = doctor.rating or 4.9

    # Распределение звезд (заглушка)
    distribution = {
        "5": 78,
        "4": 8,
        "3": 2,
        "2": 1,
        "1": 0
    }

    return DoctorRatingResponse(
        average=rating,
        distribution=distribution
    )


@router.get("/reviews", response_model=List[DoctorReviewResponse])
def get_doctor_reviews(
        db: Session = Depends(get_db),
        current_user: User = Depends(require_doctor)
):
    """Получить последние отзывы врача"""
    doctor_id = get_doctor_id(current_user.id, db)

    # TODO: реальные отзывы из таблицы doctor_reviews
    # Пока возвращаем заглушку
    reviews = [
        {
            "id": 1,
            "patient_name": "Nodira K.",
            "rating": 5,
            "comment": "Doctor is very attentive and explains everything clearly. Highly recommended!",
            "created_at": "2 days ago"
        },
        {
            "id": 2,
            "patient_name": "Aziz R.",
            "rating": 4,
            "comment": "Great cardiologist. Took time to understand my condition and provided excellent care.",
            "created_at": "1 week ago"
        },
        {
            "id": 3,
            "patient_name": "Gulnora S.",
            "rating": 4,
            "comment": "Very professional and knowledgeable. Waiting time could be shorter though.",
            "created_at": "2 weeks ago"
        }
    ]

    return [
        DoctorReviewResponse(
            id=r["id"],
            patient_name=r["patient_name"],
            rating=r["rating"],
            comment=r["comment"],
            created_at=r["created_at"]
        )
        for r in reviews
    ]


@router.get("/history", response_model=List[DoctorHistoryItem])
def get_doctor_history(
        page: int = Query(1, ge=1),
        limit: int = Query(10, ge=1, le=50),
        db: Session = Depends(get_db),
        current_user: User = Depends(require_doctor)
):
    """Получить историю обслуживания врача"""
    doctor_id = get_doctor_id(current_user.id, db)

    offset = (page - 1) * limit

    appointments = db.query(Appointment).filter(
        Appointment.doctor_id == doctor_id,
        Appointment.status == "completed"
    ).order_by(Appointment.scheduled_at.desc()).offset(offset).limit(limit).all()

    result = []
    for apt in appointments:
        patient = db.query(Patient).filter(Patient.id == apt.patient_id).first()
        patient_user = db.query(User).filter(User.id == patient.user_id).first() if patient else None

        result.append(DoctorHistoryItem(
            id=apt.id,
            patient_name=patient_user.full_name if patient_user else "Unknown",
            service_type=apt.type or "Consultation",
            diagnosis=apt.reason or "General checkup",
            treatment="Prescribed medication" if apt.reason else "Lifestyle recommendations",
            date=apt.scheduled_at.strftime("%Y-%m-%d, %H:%M"),
            status="Completed"
        ))

    return result


@router.get("/demand-map")
def get_demand_map(
        db: Session = Depends(get_db),
        current_user: User = Depends(require_doctor)
):
    """Получить карту спроса по регионам"""
    doctor_id = get_doctor_id(current_user.id, db)

    # Получаем доктора для его специальности
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    specialty = doctor.specialization if doctor else "Cardiology"

    # Получаем регионы
    regions = db.query(Region).filter(Region.is_active == True).all()

    result = []
    for region in regions:
        # Количество врачей этой специальности в регионе
        doctors_count = db.query(Doctor).filter(
            Doctor.region_id == region.id,
            Doctor.specialization == specialty
        ).count()

        # Количество пациентов в регионе
        patients_count = db.query(Patient).filter(
            Patient.region_id == region.id
        ).count()

        # Рассчитываем спрос
        demand = min(95, 50 + patients_count // 100)

        result.append({
            "region": region.code,
            "name": region.name,
            "demand": demand,
            "patients": patients_count,
            "doctors": doctors_count,
            "growth": random.randint(-5, 20)
        })

    return result