from pydantic import BaseModel
from typing import Optional, List

class SymptomCategory(BaseModel):
    id: str
    name: str
    icon: Optional[str] = None
    symptoms_count: int

class SymptomItem(BaseModel):
    id: str
    name: str
    severity: str  # mild | moderate | severe

class SymptomQuestionOption(BaseModel):
    id: str
    text: str
    severity: int  # 1-5

class SymptomQuestion(BaseModel):
    id: str
    question: str
    options: List[SymptomQuestionOption]

class SymptomCheckRequest(BaseModel):
    symptom_id: str
    answers: List[dict]  # [{"question_id": "q1", "option_id": "a"}]

class SymptomCheckResponse(BaseModel):
    severity: str  # mild | moderate | severe
    score: int  # 1-10
    recommendation: str
    suggested_specialty: Optional[str] = None
    urgent: bool