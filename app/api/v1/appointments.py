from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime
from typing import Optional, List

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.appointment import Appointment
from app.models.hospital import Hospital
from app.models.region import Region
from app.schemas.appointment import (
    AppointmentCreate, AppointmentUpdate, AppointmentResponse,
    DoctorResponse, SpecialtyResponse, HospitalResponse
)

router = APIRouter(prefix="/appointments", tags=["Appointments"])


def get_patient_id(user_id: int, db: Session) -> int:
    """Получает patient_id по user_id"""
    patient = db.query(Patient).filter(Patient.user_id == user_id).first()
    if not patient:
        patient = Patient(user_id=user_id)
        db.add(patient)
        db.commit()
        db.refresh(patient)
    return patient.id


@router.get("/", response_model=List[AppointmentResponse])
def get_appointments(
        status: Optional[str] = Query(None),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Получить список записей пользователя"""
    patient_id = get_patient_id(current_user.id, db)

    query = db.query(Appointment).filter(Appointment.patient_id == patient_id)

    if status:
        query = query.filter(Appointment.status == status)
    else:
        query = query.filter(
            Appointment.status == "scheduled",
            Appointment.scheduled_at >= datetime.now()
        )

    appointments = query.order_by(Appointment.scheduled_at).all()

    result = []
    for apt in appointments:
        doctor = db.query(Doctor).filter(Doctor.id == apt.doctor_id).first()
        if not doctor:
            continue

        doctor_user = db.query(User).filter(User.id == doctor.user_id).first()
        hospital = None
        if doctor.hospital_id:
            hospital = db.query(Hospital).filter(Hospital.id == doctor.hospital_id).first()

        result.append(AppointmentResponse(
            id=apt.id,
            doctor_id=apt.doctor_id,
            doctor_name=doctor_user.full_name if doctor_user else "Dr. Unknown",
            specialty=doctor.specialization if doctor else "Unknown",
            hospital=hospital.name_en if hospital else "Tashkent Medical Center",
            hospital_id=doctor.hospital_id,
            date=apt.scheduled_at.strftime("%Y-%m-%d"),
            time=apt.scheduled_at.strftime("%H:%M"),
            status=apt.status,
            reason=apt.reason,
            type=apt.type
        ))

    return result


@router.post("/", response_model=AppointmentResponse)
def create_appointment(
        apt_data: AppointmentCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Создать новую запись к врачу"""
    patient_id = get_patient_id(current_user.id, db)

    doctor = db.query(Doctor).filter(Doctor.id == apt_data.doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    if not doctor.is_accepting_patients:
        raise HTTPException(status_code=400, detail="Doctor is not accepting patients")

    try:
        scheduled_at = datetime.strptime(f"{apt_data.date} {apt_data.time}", "%Y-%m-%d %H:%M")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date or time format")

    if scheduled_at < datetime.now():
        raise HTTPException(status_code=400, detail="Cannot book appointment in the past")

    existing = db.query(Appointment).filter(
        Appointment.doctor_id == apt_data.doctor_id,
        Appointment.scheduled_at == scheduled_at,
        Appointment.status == "scheduled"
    ).first()

    if existing:
        raise HTTPException(status_code=409, detail="Doctor is already booked at this time")

    new_appointment = Appointment(
        doctor_id=apt_data.doctor_id,
        patient_id=patient_id,
        scheduled_at=scheduled_at,
        duration_min=30,
        type=apt_data.type or "in_person",
        status="scheduled",
        reason=apt_data.reason
    )

    db.add(new_appointment)
    db.commit()
    db.refresh(new_appointment)

    doctor_user = db.query(User).filter(User.id == doctor.user_id).first()
    hospital = None
    if doctor.hospital_id:
        hospital = db.query(Hospital).filter(Hospital.id == doctor.hospital_id).first()

    return AppointmentResponse(
        id=new_appointment.id,
        doctor_id=doctor.id,
        doctor_name=doctor_user.full_name if doctor_user else "Dr. Unknown",
        specialty=doctor.specialization,
        hospital=hospital.name_en if hospital else "Tashkent Medical Center",
        hospital_id=doctor.hospital_id,
        date=scheduled_at.strftime("%Y-%m-%d"),
        time=scheduled_at.strftime("%H:%M"),
        status=new_appointment.status,
        reason=new_appointment.reason,
        type=new_appointment.type
    )


@router.get("/{appointment_id}", response_model=AppointmentResponse)
def get_appointment(
        appointment_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Получить детали записи"""
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    patient = db.query(Patient).filter(Patient.id == appointment.patient_id).first()
    if patient and patient.user_id != current_user.id:
        doctor = db.query(Doctor).filter(Doctor.id == appointment.doctor_id).first()
        if doctor and doctor.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

    doctor = db.query(Doctor).filter(Doctor.id == appointment.doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    doctor_user = db.query(User).filter(User.id == doctor.user_id).first()
    hospital = None
    if doctor.hospital_id:
        hospital = db.query(Hospital).filter(Hospital.id == doctor.hospital_id).first()

    return AppointmentResponse(
        id=appointment.id,
        doctor_id=appointment.doctor_id,
        doctor_name=doctor_user.full_name if doctor_user else "Dr. Unknown",
        specialty=doctor.specialization,
        hospital=hospital.name_en if hospital else "Tashkent Medical Center",
        hospital_id=doctor.hospital_id,
        date=appointment.scheduled_at.strftime("%Y-%m-%d"),
        time=appointment.scheduled_at.strftime("%H:%M"),
        status=appointment.status,
        reason=appointment.reason,
        type=appointment.type
    )


@router.patch("/{appointment_id}", response_model=AppointmentResponse)
def update_appointment(
        appointment_id: int,
        update_data: AppointmentUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Обновить запись"""
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    patient = db.query(Patient).filter(Patient.id == appointment.patient_id).first()
    if patient and patient.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    if update_data.status:
        if update_data.status not in ["scheduled", "completed", "cancelled", "rescheduled"]:
            raise HTTPException(status_code=400, detail="Invalid status")
        appointment.status = update_data.status

    if update_data.date and update_data.time:
        try:
            new_time = datetime.strptime(f"{update_data.date} {update_data.time}", "%Y-%m-%d %H:%M")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date or time format")

        existing = db.query(Appointment).filter(
            Appointment.doctor_id == appointment.doctor_id,
            Appointment.scheduled_at == new_time,
            Appointment.id != appointment_id,
            Appointment.status == "scheduled"
        ).first()

        if existing:
            raise HTTPException(status_code=409, detail="Doctor is already booked at this time")

        appointment.scheduled_at = new_time
        appointment.status = "rescheduled"

    db.commit()
    db.refresh(appointment)

    doctor = db.query(Doctor).filter(Doctor.id == appointment.doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    doctor_user = db.query(User).filter(User.id == doctor.user_id).first()
    hospital = None
    if doctor.hospital_id:
        hospital = db.query(Hospital).filter(Hospital.id == doctor.hospital_id).first()

    return AppointmentResponse(
        id=appointment.id,
        doctor_id=appointment.doctor_id,
        doctor_name=doctor_user.full_name if doctor_user else "Dr. Unknown",
        specialty=doctor.specialization,
        hospital=hospital.name_en if hospital else "Tashkent Medical Center",
        hospital_id=doctor.hospital_id,
        date=appointment.scheduled_at.strftime("%Y-%m-%d"),
        time=appointment.scheduled_at.strftime("%H:%M"),
        status=appointment.status,
        reason=appointment.reason,
        type=appointment.type
    )


@router.delete("/{appointment_id}")
def cancel_appointment(
        appointment_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Отменить запись"""
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    patient = db.query(Patient).filter(Patient.id == appointment.patient_id).first()
    if patient and patient.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    appointment.status = "cancelled"
    db.commit()

    return {"success": True, "message": "Appointment cancelled"}


@router.get("/calendar")
def get_calendar(
        month: str = Query(..., description="Month in YYYY-MM format"),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Получить календарь записей на месяц"""
    patient_id = get_patient_id(current_user.id, db)

    try:
        year, month_num = map(int, month.split("-"))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid month format. Use YYYY-MM")

    start_date = datetime(year, month_num, 1)
    if month_num == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month_num + 1, 1)

    appointments = db.query(Appointment).filter(
        Appointment.patient_id == patient_id,
        Appointment.scheduled_at >= start_date,
        Appointment.scheduled_at < end_date,
        Appointment.status == "scheduled"
    ).all()

    calendar_result = {}
    for apt in appointments:
        day = apt.scheduled_at.strftime("%Y-%m-%d")
        if day not in calendar_result:
            calendar_result[day] = []
        calendar_result[day].append({
            "id": apt.id,
            "time": apt.scheduled_at.strftime("%H:%M"),
            "doctor_id": apt.doctor_id
        })

    return calendar_result


@router.get("/doctors", response_model=List[DoctorResponse])
def get_doctors(
        specialty: Optional[str] = Query(None),
        region: Optional[str] = Query(None),
        q: Optional[str] = Query(None),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Получить список врачей для записи"""
    query = db.query(Doctor).filter(Doctor.is_accepting_patients == True)

    if specialty:
        query = query.filter(Doctor.specialization.ilike(f"%{specialty}%"))

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
        hospital = None
        if doctor.hospital_id:
            hospital = db.query(Hospital).filter(Hospital.id == doctor.hospital_id).first()

        result.append(DoctorResponse(
            id=doctor.id,
            name=user.full_name if user else "Dr. Unknown",
            specialty=doctor.specialization,
            hospital=hospital.name_en if hospital else "Tashkent Medical Center",
            hospital_id=doctor.hospital_id,
            rating=doctor.rating or 4.5,
            avatar=None,
            next_available=None
        ))

    return result


@router.get("/specialties", response_model=List[SpecialtyResponse])
def get_specialties(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Получить список специальностей"""
    specialties = db.query(Doctor.specialization).distinct().all()

    result = []
    for idx, spec in enumerate(specialties):
        result.append(SpecialtyResponse(
            id=f"spec_{idx + 1}",
            name=spec[0] if spec and spec[0] else "Unknown",
            icon=None
        ))

    return result


@router.get("/hospitals", response_model=List[HospitalResponse])
def get_hospitals(
        region: Optional[str] = Query(None),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Получить список больниц"""
    query = db.query(Hospital).filter(Hospital.is_active == True)

    if region:
        query = query.join(Hospital.region).filter(Region.name_en == region)

    hospitals = query.limit(50).all()

    result = []
    for hospital in hospitals:
        doctor_count = db.query(Doctor).filter(Doctor.hospital_id == hospital.id).count()
        region_name = hospital.region.name_en if hospital.region else ""

        result.append(HospitalResponse(
            id=hospital.id,
            name=hospital.name_en,
            region=region_name,
            doctors=doctor_count,
            patients=0,
            occupancy=70,
            address=hospital.full_address,
            phone=hospital.registration_phone,
            rating=hospital.rating
        ))

    return result