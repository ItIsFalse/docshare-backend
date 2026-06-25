from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AppointmentBase(BaseModel):
    doctor_id: int
    date: str  # YYYY-MM-DD
    time: str  # HH:MM
    reason: Optional[str] = None
    type: Optional[str] = "in_person"  # in_person | video


class AppointmentCreate(AppointmentBase):
    pass


class AppointmentUpdate(BaseModel):
    date: Optional[str] = None
    time: Optional[str] = None
    status: Optional[str] = None  # scheduled | completed | cancelled | rescheduled


class AppointmentResponse(BaseModel):
    id: int
    doctor_id: int
    doctor_name: str
    specialty: str
    hospital: str
    date: str
    time: str
    status: str
    reason: Optional[str] = None
    type: str

    class Config:
        from_attributes = True


class DoctorResponse(BaseModel):
    id: int
    name: str
    specialty: str
    hospital: str
    rating: float
    avatar: Optional[str] = None
    next_available: Optional[str] = None


class SpecialtyResponse(BaseModel):
    id: str
    name: str
    icon: Optional[str] = None  # <-- ДОБАВЬТЕ ЭТО ПОЛЕ


class HospitalResponse(BaseModel):
    id: int
    name: str
    region: str
    doctors: int
    patients: int
    occupancy: int