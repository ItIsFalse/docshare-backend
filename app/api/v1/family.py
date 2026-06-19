from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, date
from typing import Optional, List
import json

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.patient import Patient
from app.models.family_member import FamilyMember
from app.schemas.family import (
    FamilyMemberCreate, FamilyMemberUpdate, FamilyMemberResponse,
    FamilySummaryResponse
)

router = APIRouter(prefix="/family", tags=["Family"])


def get_patient_id(user_id: int, db: Session) -> int:
    """Получает patient_id по user_id"""
    patient = db.query(Patient).filter(Patient.user_id == user_id).first()
    if not patient:
        patient = Patient(user_id=user_id)
        db.add(patient)
        db.commit()
        db.refresh(patient)
    return patient.id


def parse_date(date_str: Optional[str]) -> Optional[date]:
    """Парсит дату из строки YYYY-MM-DD"""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return None


def format_date(dt: Optional[date]) -> Optional[str]:
    """Форматирует дату в строку YYYY-MM-DD"""
    if not dt:
        return None
    return dt.strftime("%Y-%m-%d")


@router.get("/", response_model=List[FamilyMemberResponse])
def get_family(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Получить список членов семьи"""
    patient_id = get_patient_id(current_user.id, db)

    members = db.query(FamilyMember).filter(
        FamilyMember.patient_id == patient_id,
        FamilyMember.status == "active"
    ).all()

    result = []
    for member in members:
        # Парсим JSON поля
        allergies = []
        chronic_conditions = []
        if member.allergies:
            try:
                allergies = json.loads(member.allergies)
            except:
                allergies = []
        if member.chronic_conditions:
            try:
                chronic_conditions = json.loads(member.chronic_conditions)
            except:
                chronic_conditions = []

        result.append(FamilyMemberResponse(
            id=member.id,
            patient_id=member.patient_id,
            name=member.name or "Unknown",
            relation=member.relationship_type or "other",
            date_of_birth=format_date(member.date_of_birth),
            gender=member.gender,
            blood_type=member.blood_type,
            allergies=allergies,
            chronic_conditions=chronic_conditions,
            health_status=member.health_status or "good",
            avatar=None,
            last_checkup=format_date(member.last_checkup),
            health_score=member.health_score
        ))

    return result


@router.post("/", response_model=FamilyMemberResponse)
def add_family_member(
        member_data: FamilyMemberCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Добавить нового члена семьи"""
    patient_id = get_patient_id(current_user.id, db)

    # Проверяем, не превышен ли лимит (опционально)
    count = db.query(FamilyMember).filter(
        FamilyMember.patient_id == patient_id,
        FamilyMember.status == "active"
    ).count()

    if count >= 10:
        raise HTTPException(status_code=400, detail="Maximum 10 family members allowed")

    # Создаем нового члена семьи
    new_member = FamilyMember(
        patient_id=patient_id,
        name=member_data.name,
        relationship_type=member_data.relation,
        date_of_birth=parse_date(member_data.date_of_birth),
        gender=member_data.gender,
        blood_type=member_data.blood_type,
        allergies=json.dumps(member_data.allergies) if member_data.allergies else None,
        chronic_conditions=json.dumps(member_data.chronic_conditions) if member_data.chronic_conditions else None,
        health_status=member_data.health_status or "good",
        health_score=80,  # По умолчанию
        status="active"
    )

    db.add(new_member)
    db.commit()
    db.refresh(new_member)

    return FamilyMemberResponse(
        id=new_member.id,
        patient_id=new_member.patient_id,
        name=new_member.name or "Unknown",
        relation=new_member.relationship_type or "other",
        date_of_birth=format_date(new_member.date_of_birth),
        gender=new_member.gender,
        blood_type=new_member.blood_type,
        allergies=member_data.allergies or [],
        chronic_conditions=member_data.chronic_conditions or [],
        health_status=new_member.health_status or "good",
        avatar=None,
        last_checkup=format_date(new_member.last_checkup),
        health_score=new_member.health_score
    )


@router.get("/summary", response_model=FamilySummaryResponse)
def get_family_summary(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Получить статистику по семье"""
    patient_id = get_patient_id(current_user.id, db)

    members = db.query(FamilyMember).filter(
        FamilyMember.patient_id == patient_id,
        FamilyMember.status == "active"
    ).all()

    total = len(members)
    good = 0
    attention = 0
    critical = 0
    total_score = 0

    for member in members:
        status = member.health_status or "good"
        if status == "good":
            good += 1
        elif status == "attention":
            attention += 1
        elif status == "critical":
            critical += 1
        total_score += member.health_score or 80

    average_score = int(total_score / total) if total > 0 else 0

    return FamilySummaryResponse(
        average_score=average_score,
        members_good=good,
        members_attention=attention,
        members_critical=critical,
        total_members=total
    )


@router.get("/{member_id}", response_model=FamilyMemberResponse)
def get_family_member(
        member_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Получить детали члена семьи"""
    patient_id = get_patient_id(current_user.id, db)

    member = db.query(FamilyMember).filter(
        FamilyMember.id == member_id,
        FamilyMember.patient_id == patient_id
    ).first()

    if not member:
        raise HTTPException(status_code=404, detail="Family member not found")

    allergies = []
    chronic_conditions = []
    if member.allergies:
        try:
            allergies = json.loads(member.allergies)
        except:
            allergies = []
    if member.chronic_conditions:
        try:
            chronic_conditions = json.loads(member.chronic_conditions)
        except:
            chronic_conditions = []

    return FamilyMemberResponse(
        id=member.id,
        patient_id=member.patient_id,
        name=member.name or "Unknown",
        relation=member.relationship_type or "other",
        date_of_birth=format_date(member.date_of_birth),
        gender=member.gender,
        blood_type=member.blood_type,
        allergies=allergies,
        chronic_conditions=chronic_conditions,
        health_status=member.health_status or "good",
        avatar=None,
        last_checkup=format_date(member.last_checkup),
        health_score=member.health_score
    )


@router.patch("/{member_id}", response_model=FamilyMemberResponse)
def update_family_member(
        member_id: int,
        update_data: FamilyMemberUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Обновить информацию о члене семьи"""
    patient_id = get_patient_id(current_user.id, db)

    member = db.query(FamilyMember).filter(
        FamilyMember.id == member_id,
        FamilyMember.patient_id == patient_id
    ).first()

    if not member:
        raise HTTPException(status_code=404, detail="Family member not found")

    # Обновляем поля
    if update_data.name is not None:
        member.name = update_data.name
    if update_data.relation is not None:
        member.relationship_type = update_data.relation
    if update_data.date_of_birth is not None:
        member.date_of_birth = parse_date(update_data.date_of_birth)
    if update_data.gender is not None:
        member.gender = update_data.gender
    if update_data.blood_type is not None:
        member.blood_type = update_data.blood_type
    if update_data.allergies is not None:
        member.allergies = json.dumps(update_data.allergies)
    if update_data.chronic_conditions is not None:
        member.chronic_conditions = json.dumps(update_data.chronic_conditions)
    if update_data.health_status is not None:
        member.health_status = update_data.health_status

    db.commit()
    db.refresh(member)

    allergies = []
    chronic_conditions = []
    if member.allergies:
        try:
            allergies = json.loads(member.allergies)
        except:
            allergies = []
    if member.chronic_conditions:
        try:
            chronic_conditions = json.loads(member.chronic_conditions)
        except:
            chronic_conditions = []

    return FamilyMemberResponse(
        id=member.id,
        patient_id=member.patient_id,
        name=member.name or "Unknown",
        relation=member.relationship_type or "other",
        date_of_birth=format_date(member.date_of_birth),
        gender=member.gender,
        blood_type=member.blood_type,
        allergies=allergies,
        chronic_conditions=chronic_conditions,
        health_status=member.health_status or "good",
        avatar=None,
        last_checkup=format_date(member.last_checkup),
        health_score=member.health_score
    )


@router.delete("/{member_id}")
def delete_family_member(
        member_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Удалить члена семьи (мягкое удаление)"""
    patient_id = get_patient_id(current_user.id, db)

    member = db.query(FamilyMember).filter(
        FamilyMember.id == member_id,
        FamilyMember.patient_id == patient_id
    ).first()

    if not member:
        raise HTTPException(status_code=404, detail="Family member not found")

    # Мягкое удаление
    member.status = "inactive"
    db.commit()

    return {"success": True, "message": "Family member removed"}


@router.get("/{member_id}/health")
def get_member_health(
        member_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Получить данные о здоровье члена семьи"""
    patient_id = get_patient_id(current_user.id, db)

    member = db.query(FamilyMember).filter(
        FamilyMember.id == member_id,
        FamilyMember.patient_id == patient_id
    ).first()

    if not member:
        raise HTTPException(status_code=404, detail="Family member not found")

    # TODO: добавить реальные данные о здоровье
    return {
        "member_id": member.id,
        "name": member.name,
        "health_status": member.health_status or "good",
        "health_score": member.health_score or 80,
        "last_checkup": format_date(member.last_checkup),
        "blood_type": member.blood_type,
        "allergies": json.loads(member.allergies) if member.allergies else [],
        "chronic_conditions": json.loads(member.chronic_conditions) if member.chronic_conditions else [],
        "recent_vitals": []  # TODO: добавить витальные показатели
    }