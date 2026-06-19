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

    # Если категорий нет, создаем тестовые
    if not categories:
        return _create_default_categories(db)

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
        # Пробуем найти категорию по имени или id
        cat = db.query(SymptomCategory).filter(
            (SymptomCategory.name == category) |
            (SymptomCategory.id == int(category) if category.isdigit() else False)
        ).first()

        if cat:
            query = query.filter(Symptom.category_id == cat.id)

    symptoms = query.all()

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

    # Пробуем найти симптом по id или name
    symptom = db.query(Symptom).filter(
        (Symptom.id == int(symptom_id) if symptom_id.isdigit() else False) |
        (Symptom.name == symptom_id)
    ).first()

    if not symptom:
        raise HTTPException(status_code=404, detail="Symptom not found")

    questions = db.query(SymptomQuestion).filter(
        SymptomQuestion.symptom_id == symptom.id
    ).all()

    # Если вопросов нет, создаем тестовые
    if not questions:
        return _create_test_questions(symptom)

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

    # Находим симптом
    symptom = db.query(Symptom).filter(
        (Symptom.id == int(check_data.symptom_id) if check_data.symptom_id.isdigit() else False) |
        (Symptom.name == check_data.symptom_id)
    ).first()

    if not symptom:
        raise HTTPException(status_code=404, detail="Symptom not found")

    # Рассчитываем severity на основе ответов
    total_severity = 0
    for answer in check_data.answers:
        # Находим вопрос
        question = db.query(SymptomQuestion).filter(
            SymptomQuestion.id == int(answer.get("question_id", 0))
        ).first()

        if question:
            # Находим опцию
            for opt in question.options:
                if opt["id"] == answer.get("option_id"):
                    total_severity += opt.get("severity", 1)
                    break

    # Определяем уровень
    if total_severity <= 3:
        severity = "mild"
        score = random.randint(2, 4)
        recommendation = "Monitor your symptoms for 48 hours. Rest and stay hydrated."
        urgent = False
        suggested_specialty = "General Practice"
    elif total_severity <= 6:
        severity = "moderate"
        score = random.randint(5, 7)
        recommendation = "Schedule a doctor's appointment within 2-3 days. Avoid strenuous activity."
        urgent = False
        suggested_specialty = _get_specialty_for_symptom(symptom.name)
    else:
        severity = "severe"
        score = random.randint(8, 10)
        recommendation = "Seek immediate medical attention. Visit emergency room or call emergency services."
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

def _create_default_categories(db: Session) -> List[SymptomCategorySchema]:
    """Создает тестовые категории симптомов"""

    categories_data = [
        {"name": "General Symptoms", "icon": "🩺", "description": "Common general symptoms"},
        {"name": "Respiratory", "icon": "🫁", "description": "Breathing and respiratory issues"},
        {"name": "Heart & Circulation", "icon": "❤️", "description": "Cardiovascular symptoms"},
        {"name": "Digestive", "icon": "🍽️", "description": "Digestive system issues"},
        {"name": "Muscles & Joints", "icon": "💪", "description": "Musculoskeletal symptoms"},
        {"name": "Head & Mind", "icon": "🧠", "description": "Neurological and mental symptoms"},
        {"name": "Skin & Allergies", "icon": "🧴", "description": "Skin conditions and allergies"},
        {"name": "Urinary", "icon": "🚽", "description": "Urinary system issues"}
    ]

    created = []
    for cat_data in categories_data:
        existing = db.query(SymptomCategory).filter(SymptomCategory.name == cat_data["name"]).first()
        if not existing:
            new_cat = SymptomCategory(**cat_data)
            db.add(new_cat)
            db.flush()
            created.append(new_cat)
        else:
            created.append(existing)

    db.commit()

    # Создаем тестовые симптомы для каждой категории
    symptoms_data = {
        "General Symptoms": ["Fever", "Fatigue", "Headache", "Chills", "Night Sweats"],
        "Respiratory": ["Cough", "Shortness of Breath", "Wheezing", "Chest Congestion", "Sore Throat"],
        "Heart & Circulation": ["Chest Pain", "Palpitations", "High Blood Pressure", "Dizziness"],
        "Digestive": ["Nausea", "Vomiting", "Abdominal Pain", "Diarrhea", "Constipation"],
        "Muscles & Joints": ["Joint Pain", "Muscle Aches", "Back Pain", "Stiffness"],
        "Head & Mind": ["Migraine", "Anxiety", "Dizziness", "Brain Fog", "Depression"],
        "Skin & Allergies": ["Rash", "Itching", "Hives", "Eczema", "Allergic Reaction"],
        "Urinary": ["Painful Urination", "Frequent Urination", "Blood in Urine"]
    }

    for cat_name, symptom_names in symptoms_data.items():
        cat = db.query(SymptomCategory).filter(SymptomCategory.name == cat_name).first()
        if cat:
            for symptom_name in symptom_names:
                existing = db.query(Symptom).filter(
                    Symptom.category_id == cat.id,
                    Symptom.name == symptom_name
                ).first()
                if not existing:
                    new_symptom = Symptom(
                        category_id=cat.id,
                        name=symptom_name,
                        severity="mild"
                    )
                    db.add(new_symptom)

    db.commit()

    # Возвращаем результат
    result = []
    for cat in created:
        symptoms_count = db.query(Symptom).filter(Symptom.category_id == cat.id).count()
        result.append(SymptomCategorySchema(
            id=str(cat.id),
            name=cat.name,
            icon=cat.icon,
            symptoms_count=symptoms_count
        ))

    return result


def _create_test_questions(symptom: Symptom) -> List[SymptomQuestionSchema]:
    """Создает тестовые вопросы для симптома"""

    questions_data = {
        "Cough": [
            {
                "question": "How long have you had the cough?",
                "options": [
                    {"id": "a", "text": "Less than 24 hours", "severity": 1},
                    {"id": "b", "text": "1-3 days", "severity": 2},
                    {"id": "c", "text": "More than 3 days", "severity": 3}
                ]
            },
            {
                "question": "Is the cough productive (with phlegm)?",
                "options": [
                    {"id": "a", "text": "No, dry cough", "severity": 1},
                    {"id": "b", "text": "Yes, clear phlegm", "severity": 2},
                    {"id": "c", "text": "Yes, colored phlegm", "severity": 3}
                ]
            }
        ],
        "Fever": [
            {
                "question": "What is your temperature?",
                "options": [
                    {"id": "a", "text": "Below 38°C", "severity": 1},
                    {"id": "b", "text": "38-39°C", "severity": 2},
                    {"id": "c", "text": "Above 39°C", "severity": 3}
                ]
            },
            {
                "question": "How long have you had the fever?",
                "options": [
                    {"id": "a", "text": "Less than 24 hours", "severity": 1},
                    {"id": "b", "text": "1-3 days", "severity": 2},
                    {"id": "c", "text": "More than 3 days", "severity": 3}
                ]
            }
        ],
        "Chest Pain": [
            {
                "question": "What type of pain are you experiencing?",
                "options": [
                    {"id": "a", "text": "Mild discomfort", "severity": 1},
                    {"id": "b", "text": "Sharp pain", "severity": 2},
                    {"id": "c", "text": "Tightness or pressure", "severity": 3}
                ]
            },
            {
                "question": "Does the pain spread to other areas?",
                "options": [
                    {"id": "a", "text": "No, stays in chest", "severity": 1},
                    {"id": "b", "text": "Yes, to left arm", "severity": 2},
                    {"id": "c", "text": "Yes, to jaw or back", "severity": 3}
                ]
            }
        ],
        "Headache": [
            {
                "question": "What type of headache is it?",
                "options": [
                    {"id": "a", "text": "Dull, aching pain", "severity": 1},
                    {"id": "b", "text": "Throbbing pain", "severity": 2},
                    {"id": "c", "text": "Sharp, stabbing pain", "severity": 3}
                ]
            }
        ]
    }

    # Используем стандартные вопросы, если для симптома нет специальных
    default_questions = [
        {
            "question": "How severe is your symptom?",
            "options": [
                {"id": "a", "text": "Mild", "severity": 1},
                {"id": "b", "text": "Moderate", "severity": 2},
                {"id": "c", "text": "Severe", "severity": 3}
            ]
        },
        {
            "question": "How long have you had this symptom?",
            "options": [
                {"id": "a", "text": "Less than 24 hours", "severity": 1},
                {"id": "b", "text": "1-3 days", "severity": 2},
                {"id": "c", "text": "More than 3 days", "severity": 3}
            ]
        }
    ]

    q_data = questions_data.get(symptom.name, default_questions)

    result = []
    for idx, q in enumerate(q_data):
        options = [
            SymptomQuestionOption(
                id=opt["id"],
                text=opt["text"],
                severity=opt["severity"]
            )
            for opt in q["options"]
        ]

        result.append(SymptomQuestionSchema(
            id=f"q_{idx + 1}",
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