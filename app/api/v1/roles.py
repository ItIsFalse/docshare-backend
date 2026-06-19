from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from ...core.database import get_db
from ...core.dependencies import require_super_admin
from ...models.user import User
from ...models.role import Role

router = APIRouter(prefix="/roles", tags=["Roles"])


@router.get("/")
def get_roles(
        db: Session = Depends(get_db),
        current_user: User = Depends(require_super_admin)
):
    """Получение списка всех ролей (только суперадмин)"""
    roles = db.query(Role).all()
    return [
        {"id": r.id, "name": r.name, "description": r.description}
        for r in roles
    ]


@router.post("/init")
def init_roles(
        db: Session = Depends(get_db),
        current_user: User = Depends(require_super_admin)
):
    """Инициализация ролей (только суперадмин)"""
    default_roles = [
        {"name": "citizen", "description": "Обычный пользователь"},
        {"name": "doctor", "description": "Врач"},
        {"name": "regional_admin", "description": "Региональный администратор"},
        {"name": "national_admin", "description": "Национальный администратор"}
    ]

    for role_data in default_roles:
        existing = db.query(Role).filter(Role.name == role_data["name"]).first()
        if not existing:
            new_role = Role(**role_data)
            db.add(new_role)

    db.commit()
    return {"success": True, "message": "Roles initialized"}