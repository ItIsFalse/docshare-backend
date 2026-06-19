from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class DoctorScheduleItem(BaseModel):
    id: int
    patient_name: str
    time: str
    type: str  # video | in_person
    reason: Optional[str] = None
    status: str

class DoctorRequestItem(BaseModel):
    id: int
    patient_name: str
    age: int
    reason: str
    date: str
    time: str
    created_at: str

class DoctorStatsResponse(BaseModel):
    patients_today: int
    consultations_week: int
    rating: float
    pending_requests: int
    total_patients: int
    growth_percent: float

class DoctorRatingResponse(BaseModel):
    average: float
    distribution: dict  # {5: 78, 4: 8, 3: 2, 2: 1, 1: 0}

class DoctorReviewResponse(BaseModel):
    id: int
    patient_name: str
    rating: int
    comment: str
    created_at: str

class DoctorHistoryItem(BaseModel):
    id: int
    patient_name: str
    service_type: str
    diagnosis: str
    treatment: str
    date: str
    status: str