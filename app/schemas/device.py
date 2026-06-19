from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class DeviceBase(BaseModel):
    name: str
    type: str  # smartwatch, fitness_band, blood_pressure_monitor, glucose_monitor
    mac: Optional[str] = None


class DeviceCreate(DeviceBase):
    pass


class DeviceResponse(DeviceBase):
    id: int
    patient_id: int
    connected: bool
    last_sync: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True