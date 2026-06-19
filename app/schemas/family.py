from pydantic import BaseModel, field_validator
from typing import Optional, List


class FamilyMemberBase(BaseModel):
    name: str
    relation: str
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    blood_type: Optional[str] = None
    allergies: Optional[List[str]] = []
    chronic_conditions: Optional[List[str]] = []
    health_status: Optional[str] = "good"

    @field_validator('name')
    def name_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        return v

    @field_validator('relation')
    def relation_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Relation cannot be empty')
        return v


class FamilyMemberCreate(FamilyMemberBase):
    pass


class FamilyMemberUpdate(BaseModel):
    name: Optional[str] = None
    relation: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    blood_type: Optional[str] = None
    allergies: Optional[List[str]] = None
    chronic_conditions: Optional[List[str]] = None
    health_status: Optional[str] = None


class FamilyMemberResponse(FamilyMemberBase):
    id: int
    patient_id: int
    avatar: Optional[str] = None
    last_checkup: Optional[str] = None
    health_score: Optional[int] = None

    class Config:
        from_attributes = True


class FamilySummaryResponse(BaseModel):
    average_score: int
    members_good: int
    members_attention: int
    members_critical: int
    total_members: int