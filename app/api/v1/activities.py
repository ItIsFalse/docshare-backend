from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timedelta
from typing import Optional, List

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.patient import Patient
from app.models.activity import Activity
from app.models.health_metric import HealthMetric
from app.schemas.activity import (
    ActivityCreate, ActivityToggle, ActivityResponse, ActivityStatsResponse
)

router = APIRouter(prefix="/activity", tags=["Activities"])


def get_patient_id(user_id: int, db: Session) -> int:
    """Получает patient_id по user_id"""
    patient = db.query(Patient).filter(Patient.user_id == user_id).first()
    if not patient:
        patient = Patient(user_id=user_id)
        db.add(patient)
        db.commit()
        db.refresh(patient)
    return patient.id


@router.get("/", response_model=List[ActivityResponse])
def get_activities(
        date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Получить список ежедневных целей"""
    patient_id = get_patient_id(current_user.id, db)

    query = db.query(Activity).filter(Activity.patient_id == patient_id)

    if date:
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d")
            start_date = target_date.replace(hour=0, minute=0, second=0)
            end_date = target_date.replace(hour=23, minute=59, second=59)
            query = query.filter(Activity.activity_date >= start_date, Activity.activity_date <= end_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    else:
        today = datetime.now().replace(hour=0, minute=0, second=0)
        query = query.filter(Activity.activity_date >= today)

    activities = query.order_by(Activity.id).all()

    return [
        ActivityResponse(
            id=a.id,
            patient_id=a.patient_id,
            title=a.title,
            description=a.description,
            category=a.category,
            duration_minutes=a.duration_minutes,
            completed=a.completed,
            streak=a.streak,
            activity_date=a.activity_date,
            completed_at=a.completed_at,
            created_at=a.created_at
        )
        for a in activities
    ]


@router.post("/", response_model=ActivityResponse)
def create_activity(
        activity_data: ActivityCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Создать новую ежедневную цель"""
    patient_id = get_patient_id(current_user.id, db)

    today = datetime.now().replace(hour=0, minute=0, second=0)
    existing = db.query(Activity).filter(
        Activity.patient_id == patient_id,
        Activity.title == activity_data.title,
        Activity.activity_date >= today
    ).first()

    if existing:
        raise HTTPException(status_code=409, detail="This activity already exists for today")

    new_activity = Activity(
        patient_id=patient_id,
        title=activity_data.title,
        description=activity_data.description,
        category=activity_data.category or "exercise",
        duration_minutes=activity_data.duration_minutes or 0,
        activity_date=datetime.now()
    )

    db.add(new_activity)
    db.commit()
    db.refresh(new_activity)

    return ActivityResponse(
        id=new_activity.id,
        patient_id=new_activity.patient_id,
        title=new_activity.title,
        description=new_activity.description,
        category=new_activity.category,
        duration_minutes=new_activity.duration_minutes,
        completed=new_activity.completed,
        streak=new_activity.streak,
        activity_date=new_activity.activity_date,
        completed_at=new_activity.completed_at,
        created_at=new_activity.created_at
    )


@router.post("/{activity_id}/toggle", response_model=ActivityResponse)
def toggle_activity(
        activity_id: int,
        toggle_data: ActivityToggle,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Отметить цель как выполненную/невыполненную"""
    patient_id = get_patient_id(current_user.id, db)

    activity = db.query(Activity).filter(
        Activity.id == activity_id,
        Activity.patient_id == patient_id
    ).first()

    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    activity.completed = toggle_data.completed
    activity.completed_at = datetime.now() if toggle_data.completed else None

    if toggle_data.completed:
        completed_count = db.query(Activity).filter(
            Activity.patient_id == patient_id,
            Activity.completed == True,
            Activity.activity_date >= datetime.now() - timedelta(days=30)
        ).count()
        activity.streak = completed_count // 7
    else:
        activity.streak = 0

    db.commit()
    db.refresh(activity)

    return ActivityResponse(
        id=activity.id,
        patient_id=activity.patient_id,
        title=activity.title,
        description=activity.description,
        category=activity.category,
        duration_minutes=activity.duration_minutes,
        completed=activity.completed,
        streak=activity.streak,
        activity_date=activity.activity_date,
        completed_at=activity.completed_at,
        created_at=activity.created_at
    )


@router.get("/stats", response_model=ActivityStatsResponse)
def get_activity_stats(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Получить статистику активности"""
    patient_id = get_patient_id(current_user.id, db)

    steps_metric = db.query(HealthMetric).filter(
        HealthMetric.patient_id == patient_id,
        HealthMetric.metric_type == "steps"
    ).order_by(desc(HealthMetric.measured_at)).first()

    calories_metric = db.query(HealthMetric).filter(
        HealthMetric.patient_id == patient_id,
        HealthMetric.metric_type == "calories"
    ).order_by(desc(HealthMetric.measured_at)).first()

    distance_metric = db.query(HealthMetric).filter(
        HealthMetric.patient_id == patient_id,
        HealthMetric.metric_type == "distance_km"
    ).order_by(desc(HealthMetric.measured_at)).first()

    steps = int(steps_metric.value) if steps_metric else 8450
    calories = int(calories_metric.value) if calories_metric else 450
    distance_km = float(distance_metric.value) if distance_metric else 6.2

    today = datetime.now().replace(hour=0, minute=0, second=0)
    today_completed = db.query(Activity).filter(
        Activity.patient_id == patient_id,
        Activity.completed == True,
        Activity.activity_date >= today
    ).count()

    streak_metric = db.query(Activity).filter(
        Activity.patient_id == patient_id,
        Activity.completed == True
    ).count()
    day_streak = min(streak_metric // 2, 12)

    weekly_trend = [60, 80, 45, 90, 70, 85, 100]
    weekly_change_percent = 12.0

    return ActivityStatsResponse(
        steps=steps,
        steps_goal=10000,
        calories=calories,
        distance_km=distance_km,
        day_streak=day_streak,
        weekly_trend=weekly_trend,
        weekly_change_percent=weekly_change_percent
    )