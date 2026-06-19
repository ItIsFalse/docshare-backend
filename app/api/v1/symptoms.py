from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
import random

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.symptom import SymptomCategory, Symptom, SymptomQuestion
from app.schemas.symptom import (
    SymptomCategory as SymptomCategorySchema,
    SymptomItem, SymptomQuestion as SymptomQuestionSchema,
    SymptomQuestionOption, SymptomCheckRequest, SymptomCheckResponse
)

router = APIRouter(prefix="/symptoms", tags=["Symptoms"])


@router.get("/categories", response_model=List[SymptomCategorySchema])
def get_symptom_categories(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Получить категории симптомов"""

    categories = db.query(SymptomCategory).all()

    # Если категорий нет, возвращаем дефолтные без создания в БД
    if not categories:
        return _get_default_categories()

    result = []
    for cat in categories:
        symptoms_count = db.query(Symptom).filter(Symptom.category_id == cat.id).count()
        result.append(SymptomCategorySchema(
            id=str(cat.id),
            name=cat.name,
            icon=cat.icon,
            symptoms_count=symptoms_count
        ))

    return result


@router.get("/", response_model=List[SymptomItem])
def get_symptoms(
        category: Optional[str] = Query(None),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Получить симптомы по категории"""

    query = db.query(Symptom)

    if category:
        cat = db.query(SymptomCategory).filter(
            (SymptomCategory.name == category) |
            (SymptomCategory.id == int(category) if category.isdigit() else False)
        ).first()

        if cat:
            query = query.filter(Symptom.category_id == cat.id)

    symptoms = query.all()

    # Если симптомов нет, возвращаем дефолтные
    if not symptoms:
        return _get_default_symptoms(category)

    return [
        SymptomItem(
            id=str(s.id),
            name=s.name,
            severity=s.severity
        )
        for s in symptoms
    ]


@router.get("/{symptom_id}/questions", response_model=List[SymptomQuestionSchema])
def get_symptom_questions(
        symptom_id: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Получить вопросы для симптома"""

    symptom = db.query(Symptom).filter(
        (Symptom.id == int(symptom_id) if symptom_id.isdigit() else False) |
        (Symptom.name == symptom_id)
    ).first()

    if not symptom:
        raise HTTPException(status_code=404, detail="Symptom not found")

    questions = db.query(SymptomQuestion).filter(
        SymptomQuestion.symptom_id == symptom.id
    ).all()

    if not questions:
        return _get_default_questions(symptom.name)

    result = []
    for q in questions:
        options = [
            SymptomQuestionOption(
                id=opt["id"],
                text=opt["text"],
                severity=opt.get("severity", 1)
            )
            for opt in q.options
        ]

        result.append(SymptomQuestionSchema(
            id=str(q.id),
            question=q.question,
            options=options
        ))

    return result


@router.post("/check", response_model=SymptomCheckResponse)
def check_symptoms(
        check_data: SymptomCheckRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Проверить симптомы и получить оценку"""

    symptom = db.query(Symptom).filter(
        (Symptom.id == int(check_data.symptom_id) if check_data.symptom_id.isdigit() else False) |
        (Symptom.name == check_data.symptom_id)
    ).first()

    if not symptom:
        raise HTTPException(status_code=404, detail="Symptom not found")

    total_severity = 0
    for answer in check_data.answers:
        question_id = answer.get("question_id")
        option_id = answer.get("option_id")

        if question_id in ["q1", "q2"]:
            if question_id == "q1":
                total_severity += 1 if option_id == "a" else 2 if option_id == "b" else 3
            else:
                total_severity += 1 if option_id == "a" else 2 if option_id == "b" else 3
            continue

        try:
            q_id = int(question_id)
            question = db.query(SymptomQuestion).filter(SymptomQuestion.id == q_id).first()
            if question:
                for opt in question.options:
                    if opt.get("id") == option_id:
                        total_severity += opt.get("severity", 1)
                        break
        except (ValueError, TypeError):
            pass

    if total_severity <= 3:
        severity = "mild"
        score = random.randint(2, 4)
        recommendation = "Monitor your symptoms for 48 hours. Rest and stay hydrated."
        urgent = False
        suggested_specialty = "General Practice"
    elif total_severity <= 6:
        severity = "moderate"
        score = random.randint(5, 7)
        recommendation = "Schedule a doctor's appointment within 2-3 days."
        urgent = False
        suggested_specialty = _get_specialty_for_symptom(symptom.name)
    else:
        severity = "severe"
        score = random.randint(8, 10)
        recommendation = "Seek immediate medical attention!"
        urgent = True
        suggested_specialty = _get_specialty_for_symptom(symptom.name)

    return SymptomCheckResponse(
        severity=severity,
        score=score,
        recommendation=recommendation,
        suggested_specialty=suggested_specialty,
        urgent=urgent
    )


# ============= HELPER FUNCTIONS =============

def _get_default_categories() -> List[SymptomCategorySchema]:
    """Возвращает дефолтные категории (без БД)"""
    categories = [
        {"id": "general", "name": "General Symptoms", "icon": "🩺"},
        {"id": "respiratory", "name": "Respiratory", "icon": "🫁"},
        {"id": "heart", "name": "Heart & Circulation", "icon": "❤️"},
        {"id": "digestive", "name": "Digestive", "icon": "🍽️"},
        {"id": "muscles", "name": "Muscles & Joints", "icon": "💪"},
        {"id": "head", "name": "Head & Mind", "icon": "🧠"},
        {"id": "skin", "name": "Skin & Allergies", "icon": "🧴"},
        {"id": "urinary", "name": "Urinary", "icon": "🚽"}
    ]
    return [
        SymptomCategorySchema(
            id=c["id"],
            name=c["name"],
            icon=c["icon"],
            symptoms_count=5
        )
        for c in categories
    ]


def _get_default_symptoms(category: Optional[str]) -> List[SymptomItem]:
    """Возвращает дефолтные симптомы"""
    symptoms_map = {
        "General Symptoms": ["Fever", "Fatigue", "Headache", "Chills", "Night Sweats"],
        "Respiratory": ["Cough", "Shortness of Breath", "Wheezing", "Chest Congestion", "Sore Throat"],
        "Heart & Circulation": ["Chest Pain", "Palpitations", "High Blood Pressure", "Dizziness"],
        "Digestive": ["Nausea", "Vomiting", "Abdominal Pain", "Diarrhea", "Constipation"],
        "Muscles & Joints": ["Joint Pain", "Muscle Aches", "Back Pain", "Stiffness"],
        "Head & Mind": ["Migraine", "Anxiety", "Dizziness", "Brain Fog", "Depression"],
        "Skin & Allergies": ["Rash", "Itching", "Hives", "Eczema", "Allergic Reaction"],
        "Urinary": ["Painful Urination", "Frequent Urination", "Blood in Urine"]
    }

    symptoms = symptoms_map.get(category or "General Symptoms", ["Fever", "Headache", "Cough"])

    return [
        SymptomItem(
            id=s.lower().replace(" ", "_"),
            name=s,
            severity="mild"
        )
        for s in symptoms[:5]
    ]


def _get_default_questions(symptom_name: str) -> List[SymptomQuestionSchema]:
    """Возвращает дефолтные вопросы"""
    questions = [
        {
            "id": "q1",
            "question": "How severe is your symptom?",
            "options": [
                {"id": "a", "text": "Mild", "severity": 1},
                {"id": "b", "text": "Moderate", "severity": 2},
                {"id": "c", "text": "Severe", "severity": 3}
            ]
        },
        {
            "id": "q2",
            "question": "How long have you had this symptom?",
            "options": [
                {"id": "a", "text": "Less than 24 hours", "severity": 1},
                {"id": "b", "text": "1-3 days", "severity": 2},
                {"id": "c", "text": "More than 3 days", "severity": 3}
            ]
        }
    ]

    result = []
    for q in questions:
        options = [
            SymptomQuestionOption(
                id=opt["id"],
                text=opt["text"],
                severity=opt["severity"]
            )
            for opt in q["options"]
        ]

        result.append(SymptomQuestionSchema(
            id=q["id"],
            question=q["question"],
            options=options
        ))

    return result


def _get_specialty_for_symptom(symptom_name: str) -> str:
    """Определяет специальность по симптомам"""
    specialties = {
        "Cough": "Pulmonology",
        "Fever": "General Practice",
        "Chest Pain": "Cardiology",
        "Headache": "Neurology",
        "Joint Pain": "Orthopedics",
        "Rash": "Dermatology",
        "Nausea": "Gastroenterology",
        "Palpitations": "Cardiology",
        "Shortness of Breath": "Pulmonology",
        "Anxiety": "Psychiatry"
    }
    return specialties.get(symptom_name, "General Practice")