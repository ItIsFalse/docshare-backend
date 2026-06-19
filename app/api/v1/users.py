from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ...core.database import get_db
from ...core.dependencies import get_current_user, require_admin, require_super_admin
from ...models.user import User
from ...schemas.user import UserUpdate, UserRoleUpdate
from ...schemas.auth import UserResponse

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/", response_model=List[UserResponse])
def get_users(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)  # Только админы
):
    """Получение списка всех пользователей (только для админов)"""
    users = db.query(User).offset(skip).limit(limit).all()
    return [
        UserResponse(
            id=u.id,
            email=u.email,
            full_name=u.full_name,
            phone=u.phone,
            city=u.city,
            role=u.role,
            is_active=u.is_active,
            is_verified=u.is_verified
        )
        for u in users
    ]


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
        user_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)
):
    """Получение пользователя по ID (только для админов)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        city=user.city,
        role=user.role,
        is_active=user.is_active,
        is_verified=user.is_verified
    )


@router.patch("/me", response_model=UserResponse)
def update_me(
        user_data: UserUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Обновление своего профиля"""
    if user_data.full_name:
        current_user.full_name = user_data.full_name
    if user_data.phone is not None:
        current_user.phone = user_data.phone
    if user_data.city is not None:
        current_user.city = user_data.city

    db.commit()
    db.refresh(current_user)

    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        phone=current_user.phone,
        city=current_user.city,
        role=current_user.role,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified
    )


@router.patch("/{user_id}/role")
def update_user_role(
        user_id: int,
        role_data: UserRoleUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_super_admin)  # Только суперадмин
):
    """Обновление роли пользователя (только суперадмин)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Нельзя менять свою роль
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot change your own role"
        )

    # Сохраняем старую роль для аудита
    old_role = user.role

    # Обновляем роль
    user.role = role_data.role
    db.commit()

    # TODO: Добавить запись в audit_log

    return {
        "success": True,
        "message": f"Role changed from '{old_role}' to '{role_data.role}'",
        "user_id": user_id,
        "old_role": old_role,
        "new_role": role_data.role
    }


@router.patch("/{user_id}/block")
def block_user(
        user_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)
):
    """Блокировка пользователя (только админы)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot block yourself"
        )

    user.is_active = False
    db.commit()

    return {"success": True, "message": "User blocked"}


@router.patch("/{user_id}/unblock")
def unblock_user(
        user_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)
):
    """Разблокировка пользователя (только админы)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = True
    db.commit()

    return {"success": True, "message": "User unblocked"}