from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class AdminMetric(BaseModel):
    label: str
    value: int
    change: float
    unit: Optional[str] = None

class AdminAlert(BaseModel):
    id: int
    type: str  # critical, warning, info
    title: str
    message: str
    timestamp: str

class AdminRegionData(BaseModel):
    id: str
    name: str
    lat: float
    lng: float
    demand: int
    diseases: int
    hospitals: int

class AdminStatisticsResponse(BaseModel):
    region: Optional[str] = None
    disease: Optional[str] = None
    series: List[dict]
    forecast: Optional[List[dict]] = None
    unit: str

class AdminHospitalResponse(BaseModel):
    id: int
    name: str
    region: str
    doctors: int
    patients: int
    occupancy: int

class AdminDoctorResponse(BaseModel):
    id: int
    name: str
    specialization: str
    region: str
    hospital: str
    status: str
    rating: float

class AdminAuditLog(BaseModel):
    id: int
    action: str
    actor: str
    target: str
    timestamp: str
    details: Optional[str] = None