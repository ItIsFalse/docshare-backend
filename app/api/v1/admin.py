from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
from typing import Optional, List
import random

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_admin, require_super_admin
from app.models.user import User
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.appointment import Appointment
from app.models.hospital import Hospital
from app.models.region import Region
from app.models.audit_log import AuditLog
from app.schemas.admin import (
    AdminMetric, AdminAlert, AdminRegionData,
    AdminStatisticsResponse, AdminHospitalResponse,
    AdminDoctorResponse, AdminAuditLog
)

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/metrics", response_model=List[AdminMetric])
def get_admin_metrics(
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)
):
    """Получить KPI карточки для админ-панели"""

    # Всего пользователей
    total_users = db.query(User).count()

    # Активные врачи
    active_doctors = db.query(Doctor).filter(Doctor.is_accepting_patients == True).count()

    # Ожидаемые назначения
    pending_appointments = db.query(Appointment).filter(
        Appointment.status == "scheduled",
        Appointment.scheduled_at >= datetime.now()
    ).count()

    # Всего пациентов
    total_patients = db.query(Patient).count()

    # Рост (заглушка)
    growth_users = 12.5
    growth_doctors = 8.2
    growth_appointments = -5.1

    return [
        AdminMetric(
            label="Total Users",
            value=total_users,
            change=growth_users
        ),
        AdminMetric(
            label="Active Doctors",
            value=active_doctors,
            change=growth_doctors
        ),
        AdminMetric(
            label="Pending Appointments",
            value=pending_appointments,
            change=growth_appointments
        ),
        AdminMetric(
            label="Total Patients",
            value=total_patients,
            change=15.3
        )
    ]


@router.get("/alerts", response_model=List[AdminAlert])
def get_admin_alerts(
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)
):
    """Получить системные оповещения"""

    # Заглушка
    alerts = [
        {
            "id": 1,
            "type": "critical",
            "title": "Server Load High",
            "message": "Tashkent region servers at 92% capacity",
            "timestamp": "5 min ago"
        },
        {
            "id": 2,
            "type": "warning",
            "title": "Security Flag",
            "message": "Unusual login pattern detected in Samarkand",
            "timestamp": "12 min ago"
        },
        {
            "id": 3,
            "type": "info",
            "title": "System Update",
            "message": "Scheduled maintenance tonight at 02:00",
            "timestamp": "1 hour ago"
        }
    ]

    return [
        AdminAlert(
            id=a["id"],
            type=a["type"],
            title=a["title"],
            message=a["message"],
            timestamp=a["timestamp"]
        )
        for a in alerts
    ]


@router.get("/regions", response_model=List[AdminRegionData])
def get_admin_regions(
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)
):
    """Получить данные для тепловой карты регионов"""

    regions = db.query(Region).filter(Region.is_active == True).all()

    # Координаты регионов (заглушка)
    coordinates = {
        "TASH": {"lat": 41.2995, "lng": 69.2401},
        "SAM": {"lat": 39.6542, "lng": 66.9597},
        "BUK": {"lat": 39.7681, "lng": 64.4200},
        "FER": {"lat": 40.3842, "lng": 71.7843},
        "NAV": {"lat": 40.0844, "lng": 65.3792},
    }

    result = []
    for region in regions:
        coords = coordinates.get(region.code, {"lat": 40.0, "lng": 65.0})

        # Количество больниц
        hospitals_count = db.query(Hospital).filter(Hospital.region_id == region.id).count()

        # Количество заболеваний (заглушка)
        diseases_count = random.randint(20, 80)
        demand = random.randint(40, 90)

        result.append(AdminRegionData(
            id=region.code,
            name=region.name,
            lat=coords["lat"],
            lng=coords["lng"],
            demand=demand,
            diseases=diseases_count,
            hospitals=hospitals_count
        ))

    return result


@router.get("/statistics", response_model=AdminStatisticsResponse)
def get_admin_statistics(
        region: Optional[str] = Query(None),
        disease: Optional[str] = Query(None),
        from_date: Optional[str] = Query(None),
        to_date: Optional[str] = Query(None),
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)
):
    """Получить статистику для графиков"""

    # Заглушка
    series = []
    for i in range(12):
        month = f"2025-{str(i + 1).zfill(2)}"
        series.append({
            "period": month,
            "value": random.randint(100, 200)
        })

    forecast = []
    for i in range(3):
        month = f"2026-{str(i + 1).zfill(2)}"
        forecast.append({
            "period": month,
            "value": random.randint(150, 200)
        })

    return AdminStatisticsResponse(
        region=region or "National",
        disease=disease or "All",
        series=series,
        forecast=forecast,
        unit="cases"
    )


@router.get("/hospitals", response_model=List[AdminHospitalResponse])
def get_admin_hospitals(
        region: Optional[str] = Query(None),
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)
):
    """Получить список больниц"""

    query = db.query(Hospital).filter(Hospital.is_active == True)

    if region:
        query = query.join(Hospital.region).filter(Region.name_en == region)

    hospitals = query.limit(50).all()

    result = []
    for hospital in hospitals:
        doctors_count = db.query(Doctor).filter(Doctor.hospital_id == hospital.id).count()
        patients_count = db.query(Patient).filter(Patient.region_id == hospital.region_id).count()

        result.append(AdminHospitalResponse(
            id=hospital.id,
            name=hospital.name_en,
            region=hospital.region.name_en if hospital.region else "Unknown",
            doctors=doctors_count,
            patients=patients_count // 10,  # Упрощенно
            occupancy=random.randint(60, 90)
        ))

    return result


@router.post("/hospitals")
def create_hospital(
        hospital_data: dict,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_super_admin)
):
    """Создать новую больницу (только суперадмин)"""
    # TODO: реализовать создание больницы
    return {"success": True, "message": "Hospital created"}


@router.patch("/hospitals/{hospital_id}")
def update_hospital(
        hospital_id: int,
        hospital_data: dict,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)
):
    """Обновить больницу"""
    hospital = db.query(Hospital).filter(Hospital.id == hospital_id).first()
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")

    # TODO: обновить поля
    return {"success": True, "message": "Hospital updated"}


@router.delete("/hospitals/{hospital_id}")
def delete_hospital(
        hospital_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_super_admin)
):
    """Удалить больницу (только суперадмин)"""
    hospital = db.query(Hospital).filter(Hospital.id == hospital_id).first()
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")

    hospital.is_active = False
    db.commit()

    return {"success": True, "message": "Hospital deleted"}


@router.get("/doctors", response_model=List[AdminDoctorResponse])
def get_admin_doctors(
        region: Optional[str] = Query(None),
        q: Optional[str] = Query(None),
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)
):
    """Получить список врачей для управления"""

    query = db.query(Doctor)

    if region:
        query = query.join(Doctor.region).filter(Region.name_en == region)

    if q:
        query = query.join(Doctor.user).filter(
            or_(
                User.full_name.ilike(f"%{q}%"),
                Doctor.specialization.ilike(f"%{q}%")
            )
        )

    doctors = query.limit(50).all()

    result = []
    for doctor in doctors:
        user = db.query(User).filter(User.id == doctor.user_id).first()
        hospital = db.query(Hospital).filter(Hospital.id == doctor.hospital_id).first()

        result.append(AdminDoctorResponse(
            id=doctor.id,
            name=user.full_name if user else "Unknown",
            specialization=doctor.specialization,
            region=doctor.region.name_en if doctor.region else "Unknown",
            hospital=hospital.name_en if hospital else "Unknown",
            status=doctor.license_status or "active",
            rating=doctor.rating or 0.0
        ))

    return result


@router.patch("/doctors/{doctor_id}")
def update_admin_doctor(
        doctor_id: int,
        doctor_data: dict,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)
):
    """Обновить информацию о враче"""
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    # TODO: обновить поля
    return {"success": True, "message": "Doctor updated"}


@router.get("/audit-logs", response_model=List[AdminAuditLog])
def get_audit_logs(
        limit: int = Query(50, ge=1, le=100),
        db: Session = Depends(get_db),
        current_user: User = Depends(require_super_admin)
):
    """Получить логи действий (только суперадмин)"""

    # Заглушка
    logs = [
        {
            "id": 1,
            "action": "User Created",
            "actor": "Admin: John Smith",
            "target": "New User",
            "timestamp": "2 min ago",
            "details": "New doctor account created"
        },
        {
            "id": 2,
            "action": "Role Changed",
            "actor": "Admin: Sarah Lee",
            "target": "User: Dr. Kim",
            "timestamp": "15 min ago",
            "details": "Role changed from doctor to regional_admin"
        }
    ]

    return [
        AdminAuditLog(
            id=l["id"],
            action=l["action"],
            actor=l["actor"],
            target=l["target"],
            timestamp=l["timestamp"],
            details=l.get("details")
        )
        for l in logs
    ]