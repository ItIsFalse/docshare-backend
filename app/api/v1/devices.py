from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.patient import Patient
from app.models.device import Device
from app.schemas.device import DeviceCreate, DeviceResponse

router = APIRouter(prefix="/devices", tags=["Devices"])


def get_patient_id(user_id: int, db: Session) -> int:
    """Получает patient_id по user_id"""
    patient = db.query(Patient).filter(Patient.user_id == user_id).first()
    if not patient:
        patient = Patient(user_id=user_id)
        db.add(patient)
        db.commit()
        db.refresh(patient)
    return patient.id


@router.get("/", response_model=List[DeviceResponse])
def get_devices(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Получить список подключенных устройств"""

    patient_id = get_patient_id(current_user.id, db)

    devices = db.query(Device).filter(Device.patient_id == patient_id).all()

    return [
        DeviceResponse(
            id=d.id,
            patient_id=d.patient_id,
            name=d.name,
            type=d.type,
            mac=d.mac,
            connected=d.connected,
            last_sync=d.last_sync,
            created_at=d.created_at
        )
        for d in devices
    ]


@router.post("/", response_model=DeviceResponse)
def register_device(
        device_data: DeviceCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Зарегистрировать новое устройство"""

    patient_id = get_patient_id(current_user.id, db)

    # Проверяем, не зарегистрировано ли уже такое устройство
    if device_data.mac:
        existing = db.query(Device).filter(Device.mac == device_data.mac).first()
        if existing:
            raise HTTPException(status_code=409, detail="Device already registered")

    new_device = Device(
        patient_id=patient_id,
        name=device_data.name,
        type=device_data.type,
        mac=device_data.mac,
        connected=True
    )

    db.add(new_device)
    db.commit()
    db.refresh(new_device)

    return DeviceResponse(
        id=new_device.id,
        patient_id=new_device.patient_id,
        name=new_device.name,
        type=new_device.type,
        mac=new_device.mac,
        connected=new_device.connected,
        last_sync=new_device.last_sync,
        created_at=new_device.created_at
    )


@router.delete("/{device_id}")
def delete_device(
        device_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Отключить устройство"""

    patient_id = get_patient_id(current_user.id, db)

    device = db.query(Device).filter(
        Device.id == device_id,
        Device.patient_id == patient_id
    ).first()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # Мягкое отключение
    device.connected = False
    db.commit()

    return {"success": True, "message": "Device disconnected"}


@router.post("/{device_id}/sync")
def sync_device(
        device_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Синхронизировать устройство (обновляет время последней синхронизации)"""

    patient_id = get_patient_id(current_user.id, db)

    device = db.query(Device).filter(
        Device.id == device_id,
        Device.patient_id == patient_id
    ).first()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    device.last_sync = datetime.now()
    device.connected = True
    db.commit()

    return {
        "success": True,
        "message": "Device synced",
        "last_sync": device.last_sync
    }