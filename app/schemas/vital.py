from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class VitalBase(BaseModel):
    hr_bpm: Optional[int] = None
    bp_sys: Optional[int] = None
    bp_dia: Optional[int] = None
    spo2: Optional[int] = None
    weight: Optional[float] = None
    temperature: Optional[float] = None
    fasting_glucose: Optional[int] = None
    steps: Optional[int] = None
    distance_km: Optional[float] = None
    calories: Optional[int] = None
    notes: Optional[str] = None


class VitalCreate(VitalBase):
    measured_at: Optional[datetime] = None


class VitalResponse(VitalBase):
    id: int
    patient_id: int
    measured_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class VitalSummaryCard(BaseModel):
    key: str
    label: str
    value: float
    unit: str
    trend_percent: float
    trend_direction: str  # up | down
    in_range: bool
    secondary_value: Optional[float] = None


class VitalSummaryResponse(BaseModel):
    cards: list[VitalSummaryCard]


class VitalSyncRequest(BaseModel):
    device_id: str
    readings: list[VitalBase]


class VitalSyncResponse(BaseModel):
    synced: int