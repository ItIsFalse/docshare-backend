from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime, date
from typing import Optional, List
import os
import shutil
import uuid

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.patient import Patient
from app.models.document import Document
from app.schemas.document import (
    DocumentCreate, DocumentUpdate, DocumentResponse, DocumentUploadResponse
)

router = APIRouter(prefix="/documents", tags=["Documents"])

# Папка для загрузки файлов
UPLOAD_DIR = "uploads/documents"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_patient_id(user_id: int, db: Session) -> int:
    """Получает patient_id по user_id"""
    patient = db.query(Patient).filter(Patient.user_id == user_id).first()
    if not patient:
        patient = Patient(user_id=user_id)
        db.add(patient)
        db.commit()
        db.refresh(patient)
    return patient.id


def save_file(file: UploadFile, user_id: int) -> tuple:
    """Сохраняет файл и возвращает (file_path, file_url, file_size)"""
    # Генерируем уникальное имя файла
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4().hex}{file_extension}"

    # Создаем папку пользователя
    user_dir = os.path.join(UPLOAD_DIR, str(user_id))
    os.makedirs(user_dir, exist_ok=True)

    file_path = os.path.join(user_dir, unique_filename)
    file_url = f"/uploads/documents/{user_id}/{unique_filename}"

    # Сохраняем файл
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_size = os.path.getsize(file_path)

    return file_path, file_url, file_size


@router.get("/", response_model=List[DocumentResponse])
def get_documents(
        q: Optional[str] = Query(None, description="Search by title or doctor name"),
        doc_type: Optional[str] = Query(None, description="Filter by document type"),
        page: int = Query(1, ge=1),
        limit: int = Query(20, ge=1, le=100),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Получить список документов с поиском и фильтрацией"""
    patient_id = get_patient_id(current_user.id, db)

    query = db.query(Document).filter(
        Document.patient_id == patient_id,
        Document.status == "active"
    )

    if q:
        query = query.filter(
            or_(
                Document.title.ilike(f"%{q}%"),
                Document.doctor_name.ilike(f"%{q}%"),
                Document.diagnosis.ilike(f"%{q}%")
            )
        )

    if doc_type:
        query = query.filter(Document.document_type == doc_type)

    # Пагинация
    offset = (page - 1) * limit
    documents = query.order_by(Document.document_date.desc()).offset(offset).limit(limit).all()

    result = []
    for doc in documents:
        result.append(DocumentResponse(
            id=doc.id,
            patient_id=doc.patient_id,
            title=doc.title,
            type=doc.document_type,
            date=doc.document_date.strftime("%Y-%m-%d"),
            doctor_name=doc.doctor_name,
            hospital=doc.hospital,
            diagnosis=doc.diagnosis,
            treatment=doc.treatment,
            notes=doc.notes,
            file_url=doc.file_url,
            file_size_kb=doc.file_size // 1024 if doc.file_size else None,
            created_at=doc.created_at
        ))

    return result


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
        document_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Получить детали документа"""
    patient_id = get_patient_id(current_user.id, db)

    document = db.query(Document).filter(
        Document.id == document_id,
        Document.patient_id == patient_id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return DocumentResponse(
        id=document.id,
        patient_id=document.patient_id,
        title=document.title,
        type=document.document_type,
        date=document.document_date.strftime("%Y-%m-%d"),
        doctor_name=document.doctor_name,
        hospital=document.hospital,
        diagnosis=document.diagnosis,
        treatment=document.treatment,
        notes=document.notes,
        file_url=document.file_url,
        file_size_kb=document.file_size // 1024 if document.file_size else None,
        created_at=document.created_at
    )


@router.post("/", response_model=DocumentResponse)
def create_document(
        document_data: DocumentCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Создать документ без файла"""
    patient_id = get_patient_id(current_user.id, db)

    try:
        doc_date = datetime.strptime(document_data.date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    new_document = Document(
        patient_id=patient_id,
        title=document_data.title,
        document_type=document_data.type,
        document_date=doc_date,
        doctor_name=document_data.doctor_name,
        hospital=document_data.hospital,
        diagnosis=document_data.diagnosis,
        treatment=document_data.treatment,
        notes=document_data.notes,
        uploaded_by=current_user.id
    )

    db.add(new_document)
    db.commit()
    db.refresh(new_document)

    return DocumentResponse(
        id=new_document.id,
        patient_id=new_document.patient_id,
        title=new_document.title,
        type=new_document.document_type,
        date=new_document.document_date.strftime("%Y-%m-%d"),
        doctor_name=new_document.doctor_name,
        hospital=new_document.hospital,
        diagnosis=new_document.diagnosis,
        treatment=new_document.treatment,
        notes=new_document.notes,
        file_url=new_document.file_url,
        file_size_kb=new_document.file_size // 1024 if new_document.file_size else None,
        created_at=new_document.created_at
    )


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
        file: UploadFile = File(...),
        title: str = Form(...),
        doc_type: str = Form(...),
        date: str = Form(...),
        doctor_name: Optional[str] = Form(None),
        hospital: Optional[str] = Form(None),
        diagnosis: Optional[str] = Form(None),
        treatment: Optional[str] = Form(None),
        notes: Optional[str] = Form(None),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Загрузить документ с файлом"""
    patient_id = get_patient_id(current_user.id, db)

    # Проверяем тип файла
    allowed_types = ["application/pdf", "image/jpeg", "image/png", "image/jpg"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"File type {file.content_type} not allowed. Allowed: PDF, JPEG, PNG"
        )

    # Проверяем размер (макс 5MB)
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 5MB limit")

    try:
        doc_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    # Сохраняем файл
    file_path, file_url, file_size = save_file(file, current_user.id)

    # Создаем запись в БД
    new_document = Document(
        patient_id=patient_id,
        title=title,
        document_type=doc_type,
        document_date=doc_date,
        doctor_name=doctor_name,
        hospital=hospital,
        diagnosis=diagnosis,
        treatment=treatment,
        notes=notes,
        file_name=file.filename,
        file_url=file_url,
        file_size=file_size,
        uploaded_by=current_user.id
    )

    db.add(new_document)
    db.commit()
    db.refresh(new_document)

    return DocumentUploadResponse(
        id=new_document.id,
        file_url=file_url,
        message="Document uploaded successfully"
    )


@router.get("/{document_id}/download")
def download_document(
        document_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Получить URL для скачивания документа"""
    patient_id = get_patient_id(current_user.id, db)

    document = db.query(Document).filter(
        Document.id == document_id,
        Document.patient_id == patient_id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if not document.file_url:
        raise HTTPException(status_code=404, detail="Document has no file attached")

    return {
        "url": document.file_url,
        "filename": document.file_name,
        "size_kb": document.file_size // 1024 if document.file_size else 0
    }


@router.patch("/{document_id}", response_model=DocumentResponse)
def update_document(
        document_id: int,
        update_data: DocumentUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Обновить информацию о документе"""
    patient_id = get_patient_id(current_user.id, db)

    document = db.query(Document).filter(
        Document.id == document_id,
        Document.patient_id == patient_id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if update_data.title is not None:
        document.title = update_data.title
    if update_data.type is not None:
        document.document_type = update_data.type
    if update_data.date is not None:
        try:
            document.document_date = datetime.strptime(update_data.date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format")
    if update_data.doctor_name is not None:
        document.doctor_name = update_data.doctor_name
    if update_data.hospital is not None:
        document.hospital = update_data.hospital
    if update_data.diagnosis is not None:
        document.diagnosis = update_data.diagnosis
    if update_data.treatment is not None:
        document.treatment = update_data.treatment
    if update_data.notes is not None:
        document.notes = update_data.notes

    db.commit()
    db.refresh(document)

    return DocumentResponse(
        id=document.id,
        patient_id=document.patient_id,
        title=document.title,
        type=document.document_type,
        date=document.document_date.strftime("%Y-%m-%d"),
        doctor_name=document.doctor_name,
        hospital=document.hospital,
        diagnosis=document.diagnosis,
        treatment=document.treatment,
        notes=document.notes,
        file_url=document.file_url,
        file_size_kb=document.file_size // 1024 if document.file_size else None,
        created_at=document.created_at
    )


@router.delete("/{document_id}")
def delete_document(
        document_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Удалить документ (мягкое удаление)"""
    patient_id = get_patient_id(current_user.id, db)

    document = db.query(Document).filter(
        Document.id == document_id,
        Document.patient_id == patient_id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    document.status = "deleted"
    db.commit()

    return {"success": True, "message": "Document deleted"}