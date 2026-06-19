from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ActivityBase(BaseModel):
    title: str
    description: Optional[str] = None
    category: Optional[str] = "exercise"  # exercise, meditation, sleep, nutrition
    duration_minutes: Optional[int] = 0


class ActivityCreate(ActivityBase):
    pass


class ActivityToggle(BaseModel):
    completed: bool


class ActivityResponse(ActivityBase):
    id: int
    patient_id: int
    completed: bool
    streak: int
    activity_date: datetime
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ActivityStatsResponse(BaseModel):
    steps: int
    steps_goal: int
    calories: int
    distance_km: float
    day_streak: int
    weekly_trend: list[int]  # [60, 80, 45, 90, 70, 85, 100]
    weekly_change_percent: float