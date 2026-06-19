from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timedelta
from typing import Optional, List

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_citizen
from app.models.user import User
from app.models.patient import Patient
from app.models.health_metric import HealthMetric
from app.schemas.vital import (
    VitalCreate, VitalResponse, VitalSummaryResponse,
    VitalSummaryCard, VitalSyncRequest, VitalSyncResponse
)

router = APIRouter(prefix="/vitals", tags=["Vitals"])


def get_patient_id(user_id: int, db: Session) -> int:
    """Получает patient_id по user_id или создает если нет"""
    patient = db.query(Patient).filter(Patient.user_id == user_id).first()
    if not patient:
        patient = Patient(user_id=user_id)
        db.add(patient)
        db.commit()
        db.refresh(patient)
    return patient.id


def get_normal_range(metric_type: str) -> tuple:
    """Возвращает нормальный диапазон для метрики"""
    ranges = {
        "heart_rate": (60, 100),
        "blood_pressure_systolic": (90, 140),
        "blood_pressure_diastolic": (60, 90),
        "spo2": (95, 100),
        "weight": (50, 120),
        "temperature": (36.0, 37.2),
        "blood_glucose": (70, 100),
        "steps": (0, 100000),
        "distance_km": (0, 50),
        "calories": (0, 10000),
    }
    return ranges.get(metric_type, (0, 0))


def get_metric_label(metric_type: str) -> str:
    """Возвращает человеческое название метрики"""
    labels = {
        "heart_rate": "Heart Rate",
        "blood_pressure_systolic": "Blood Pressure",
        "blood_pressure_diastolic": "Blood Pressure",
        "spo2": "SpO2",
        "weight": "Weight",
        "temperature": "Temperature",
        "blood_glucose": "Glucose",
        "steps": "Steps Today",
        "distance_km": "Distance",
        "calories": "Calories"
    }
    return labels.get(metric_type, metric_type)


def get_metric_unit(metric_type: str) -> str:
    """Возвращает единицу измерения для метрики"""
    units = {
        "heart_rate": "BPM",
        "blood_pressure_systolic": "mmHg",
        "blood_pressure_diastolic": "mmHg",
        "spo2": "%",
        "weight": "kg",
        "temperature": "°C",
        "blood_glucose": "mg/dL",
        "steps": "steps",
        "distance_km": "km",
        "calories": "kcal"
    }
    return units.get(metric_type, "")


@router.post("/", response_model=VitalResponse)
def create_vital(
        vital_data: VitalCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Записать новые витальные показатели"""
    patient_id = get_patient_id(current_user.id, db)

    measured_at = vital_data.measured_at or datetime.now()

    # Создаем записи для каждого показателя
    created_metrics = []
    metrics_to_create = [
        ("heart_rate", vital_data.hr_bpm),
        ("blood_pressure_systolic", vital_data.bp_sys),
        ("blood_pressure_diastolic", vital_data.bp_dia),
        ("spo2", vital_data.spo2),
        ("weight", vital_data.weight),
        ("temperature", vital_data.temperature),
        ("blood_glucose", vital_data.fasting_glucose),
        ("steps", vital_data.steps),
        ("distance_km", vital_data.distance_km),
        ("calories", vital_data.calories),
    ]

    for metric_type, value in metrics_to_create:
        if value is not None:
            metric = HealthMetric(
                patient_id=patient_id,
                metric_type=metric_type,
                value=float(value),
                unit=get_metric_unit(metric_type),
                measured_at=measured_at,
                source="manual",
                notes=vital_data.notes
            )
            db.add(metric)
            created_metrics.append(metric)

    db.commit()

    # Возвращаем первую созданную запись
    if created_metrics:
        return VitalResponse(
            id=created_metrics[0].id,
            patient_id=patient_id,
            hr_bpm=vital_data.hr_bpm,
            bp_sys=vital_data.bp_sys,
            bp_dia=vital_data.bp_dia,
            spo2=vital_data.spo2,
            weight=vital_data.weight,
            temperature=vital_data.temperature,
            fasting_glucose=vital_data.fasting_glucose,
            steps=vital_data.steps,
            distance_km=vital_data.distance_km,
            calories=vital_data.calories,
            notes=vital_data.notes,
            measured_at=measured_at,
            created_at=datetime.now()
        )

    raise HTTPException(status_code=400, detail="No valid metrics provided")


@router.get("/", response_model=List[VitalResponse])
def get_vitals(
        from_date: Optional[datetime] = Query(None),
        to_date: Optional[datetime] = Query(None),
        limit: int = Query(100, ge=1, le=500),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Получить историю витальных показателей"""
    patient_id = get_patient_id(current_user.id, db)

    query = db.query(HealthMetric).filter(
        HealthMetric.patient_id == patient_id
    )

    if from_date:
        query = query.filter(HealthMetric.measured_at >= from_date)
    if to_date:
        query = query.filter(HealthMetric.measured_at <= to_date)

    # Группируем по типу метрики и берем последние записи
    # Упрощенная версия - возвращаем все последние записи
    metrics = query.order_by(desc(HealthMetric.measured_at)).limit(limit).all()

    # Преобразуем в формат VitalResponse (группируем по времени)
    # Для простоты возвращаем сырые данные
    return [
        VitalResponse(
            id=m.id,
            patient_id=m.patient_id,
            measured_at=m.measured_at,
            created_at=m.created_at,
            **{m.metric_type: m.value}
        )
        for m in metrics
    ]


@router.get("/latest", response_model=dict)
def get_latest_vitals(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Получить последние витальные показатели"""
    patient_id = get_patient_id(current_user.id, db)

    metric_types = [
        "heart_rate", "blood_pressure_systolic", "blood_pressure_diastolic",
        "spo2", "weight", "temperature", "blood_glucose"
    ]

    latest = {}
    for metric_type in metric_types:
        metric = db.query(HealthMetric).filter(
            HealthMetric.patient_id == patient_id,
            HealthMetric.metric_type == metric_type
        ).order_by(desc(HealthMetric.measured_at)).first()

        if metric:
            latest[metric_type] = metric.value

    # Добавляем стандартные поля для ответа
    result = {
        "id": 0,
        "patient_id": patient_id,
        "measured_at": datetime.now(),
        "created_at": datetime.now(),
        **latest
    }

    return result


@router.get("/summary", response_model=VitalSummaryResponse)
def get_vitals_summary(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Получить карточки с трендами для дашборда"""
    patient_id = get_patient_id(current_user.id, db)

    metric_types = [
        "heart_rate", "blood_pressure_systolic", "spo2", "steps"
    ]

    cards = []

    for metric_type in metric_types:
        # Получаем последние 2 записи
        metrics = db.query(HealthMetric).filter(
            HealthMetric.patient_id == patient_id,
            HealthMetric.metric_type == metric_type
        ).order_by(desc(HealthMetric.measured_at)).limit(2).all()

        if metrics:
            current_value = metrics[0].value
            previous_value = metrics[1].value if len(metrics) > 1 else current_value

            # Рассчитываем тренд
            if previous_value != 0:
                trend_percent = ((current_value - previous_value) / previous_value) * 100
            else:
                trend_percent = 0

            trend_direction = "up" if trend_percent >= 0 else "down"

            # Проверяем норму
            min_val, max_val = get_normal_range(metric_type)
            in_range = min_val <= current_value <= max_val

            card = VitalSummaryCard(
                key=metric_type,
                label=get_metric_label(metric_type),
                value=current_value,
                unit=get_metric_unit(metric_type),
                trend_percent=round(abs(trend_percent), 1),
                trend_direction=trend_direction,
                in_range=in_range
            )

            # Для кровяного давления добавляем secondary_value
            if metric_type == "blood_pressure_systolic":
                # Находим диастолическое
                diastolic = db.query(HealthMetric).filter(
                    HealthMetric.patient_id == patient_id,
                    HealthMetric.metric_type == "blood_pressure_diastolic"
                ).order_by(desc(HealthMetric.measured_at)).first()

                if diastolic:
                    card.secondary_value = diastolic.value

            cards.append(card)
        else:
            # Заглушка для отсутствующих данных
            cards.append(VitalSummaryCard(
                key=metric_type,
                label=get_metric_label(metric_type),
                value=0,
                unit=get_metric_unit(metric_type),
                trend_percent=0,
                trend_direction="up",
                in_range=True
            ))

    return VitalSummaryResponse(cards=cards)


@router.post("/sync", response_model=VitalSyncResponse)
def sync_vitals(
        sync_data: VitalSyncRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Синхронизация данных с умных устройств"""
    patient_id = get_patient_id(current_user.id, db)

    synced_count = 0
    for reading in sync_data.readings:
        measured_at = reading.measured_at or datetime.now()

        metrics_to_create = [
            ("heart_rate", reading.hr_bpm),
            ("blood_pressure_systolic", reading.bp_sys),
            ("blood_pressure_diastolic", reading.bp_dia),
            ("spo2", reading.spo2),
            ("weight", reading.weight),
            ("temperature", reading.temperature),
            ("blood_glucose", reading.fasting_glucose),
            ("steps", reading.steps),
            ("distance_km", reading.distance_km),
            ("calories", reading.calories),
        ]

        for metric_type, value in metrics_to_create:
            if value is not None:
                metric = HealthMetric(
                    patient_id=patient_id,
                    metric_type=metric_type,
                    value=float(value),
                    unit=get_metric_unit(metric_type),
                    measured_at=measured_at,
                    source="watch"
                )
                db.add(metric)
                synced_count += 1

    db.commit()
    return VitalSyncResponse(synced=synced_count)