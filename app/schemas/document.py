from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime


class DocumentBase(BaseModel):
    title: str
    type: str  # report, prescription, lab_result, imaging, other
    date: str  # YYYY-MM-DD
    doctor_name: Optional[str] = None
    hospital: Optional[str] = None
    diagnosis: Optional[str] = None
    treatment: Optional[str] = None
    notes: Optional[str] = None


class DocumentCreate(DocumentBase):
    pass


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    type: Optional[str] = None
    date: Optional[str] = None
    doctor_name: Optional[str] = None
    hospital: Optional[str] = None
    diagnosis: Optional[str] = None
    treatment: Optional[str] = None
    notes: Optional[str] = None


class DocumentResponse(DocumentBase):
    id: int
    patient_id: int
    file_url: Optional[str] = None
    file_size_kb: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentUploadResponse(BaseModel):
    id: int
    file_url: str
    message: str