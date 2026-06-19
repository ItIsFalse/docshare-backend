from sqlalchemy import Column, Integer, String, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from ..core.database import Base


class SymptomCategory(Base):
    __tablename__ = "symptom_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    icon = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)


class Symptom(Base):
    __tablename__ = "symptoms"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("symptom_categories.id"), nullable=False)
    name = Column(String(100), nullable=False)
    severity = Column(String(20), default="mild")  # mild, moderate, severe
    description = Column(Text, nullable=True)

    # Relationships
    category = relationship("SymptomCategory", backref="symptoms")


class SymptomQuestion(Base):
    __tablename__ = "symptom_questions"

    id = Column(Integer, primary_key=True, index=True)
    symptom_id = Column(Integer, ForeignKey("symptoms.id"), nullable=False)
    question = Column(Text, nullable=False)
    options = Column(JSON, nullable=False)  # [{"id": "a", "text": "...", "severity": 1}]

    # Relationships
    symptom = relationship("Symptom", backref="questions")