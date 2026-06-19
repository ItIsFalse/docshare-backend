from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime
import random

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.environment import AQIResponse

router = APIRouter(prefix="/environment", tags=["Environment"])


def get_aqi_level(aqi: int) -> tuple:
    """Возвращает уровень и совет по AQI"""
    if aqi <= 50:
        return "Good", "Perfect air quality! Enjoy outdoor activities."
    elif aqi <= 100:
        return "Moderate", "Air quality is acceptable. Sensitive groups should limit prolonged outdoor exertion."
    elif aqi <= 150:
        return "Unhealthy for Sensitive Groups", "Sensitive groups should reduce outdoor activities. Consider wearing a mask."
    elif aqi <= 200:
        return "Unhealthy", "Everyone should limit prolonged outdoor exertion. Wear a mask if you go outside."
    elif aqi <= 300:
        return "Very Unhealthy", "Avoid outdoor activities. Stay indoors and use air purifier."
    else:
        return "Hazardous", "Emergency conditions! Stay indoors and avoid all outdoor activities."


@router.get("/aqi", response_model=AQIResponse)
def get_aqi(
        region: str = Query("Tashkent", description="Region name"),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Получить качество воздуха по региону"""

    # AQI зависит от региона
    region_aqi = {
        "Tashkent": random.randint(30, 160),
        "Samarkand": random.randint(25, 120),
        "Bukhara": random.randint(40, 180),
        "Fergana": random.randint(35, 150),
        "Navoi": random.randint(20, 100),
    }

    # Если регион не найден, используем случайный
    aqi = region_aqi.get(region, random.randint(30, 150))

    # Получаем уровень и совет
    level, advice = get_aqi_level(aqi)

    # Добавляем специфичный совет для региона
    if aqi > 100:
        if "Tashkent" in region:
            advice = "Wear a mask if you go outside. Consider reducing outdoor exercise."
        elif "Bukhara" in region:
            advice = "Dusty conditions. Stay hydrated and wear protective mask."

    return AQIResponse(
        region=region,
        aqi=aqi,
        level=level,
        advice=advice,
        updated_at=datetime.now()
    )