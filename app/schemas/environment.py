from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AQIResponse(BaseModel):
    region: str
    aqi: int
    level: str  # Good, Moderate, Unhealthy, Unhealthy for Sensitive Groups, Very Unhealthy, Hazardous
    advice: str
    updated_at: datetime