from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.doctor import Doctor
from app.models.hospital import Hospital
from app.schemas.appointment import DoctorResponse

router = APIRouter(prefix="/doctors", tags=["Doctors"])


@router.get("/", response_model=List[DoctorResponse])
def get_doctors(
        specialty: Optional[str] = Query(None),
        q: Optional[str] = Query(None),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Получить список врачей для записи (доступно всем авторизованным)"""
    query = db.query(Doctor).filter(Doctor.is_accepting_patients == True)

    if specialty:
        query = query.filter(Doctor.specialization.ilike(f"%{specialty}%"))

    if q:
        query = query.join(Doctor.user).filter(
            User.full_name.ilike(f"%{q}%")
        )

    doctors = query.limit(50).all()

    result = []
    for doctor in doctors:
        user = db.query(User).filter(User.id == doctor.user_id).first()
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