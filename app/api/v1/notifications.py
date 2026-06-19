from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from typing import Optional, List

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.notification import UserNotification, NotificationTemplate
from app.schemas.notification import (
    NotificationResponse, NotificationUnreadCount, PushTokenRegister
)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/", response_model=List[NotificationResponse])
def get_notifications(
        page: int = Query(1, ge=1),
        limit: int = Query(20, ge=1, le=100),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Получить список уведомлений пользователя"""

    offset = (page - 1) * limit

    notifications = db.query(UserNotification).filter(
        UserNotification.user_id == current_user.id
    ).order_by(desc(UserNotification.created_at)).offset(offset).limit(limit).all()

    result = []
    for notif in notifications:
        # Получаем шаблон
        template = db.query(NotificationTemplate).filter(
            NotificationTemplate.id == notif.template_id
        ).first()

        # Формируем заголовок и сообщение
        title = template.title_ru if template else "Уведомление"
        message = "У вас новое уведомление"

        # Если есть параметры, подставляем
        if notif.params:
            # Упрощенная подстановка
            if template and notif.params:
                title = template.title_ru
                message = notif.params.get("message", message)

        result.append(NotificationResponse(
            id=notif.id,
            type=template.type if template else "system",
            title=title,
            message=message,
            read=notif.is_read,
            created_at=notif.created_at,
            related_type=notif.related_type,
            related_id=notif.related_id
        ))

    return result


@router.get("/unread-count", response_model=NotificationUnreadCount)
def get_unread_count(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Получить количество непрочитанных уведомлений"""

    count = db.query(UserNotification).filter(
        UserNotification.user_id == current_user.id,
        UserNotification.is_read == False
    ).count()

    return NotificationUnreadCount(count=count)


@router.post("/{notification_id}/read")
def mark_as_read(
        notification_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Отметить уведомление как прочитанное"""

    notification = db.query(UserNotification).filter(
        UserNotification.id == notification_id,
        UserNotification.user_id == current_user.id
    ).first()

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.is_read = True
    notification.read_at = datetime.now()
    db.commit()

    return {"success": True, "message": "Notification marked as read"}


@router.post("/read-all")
def mark_all_as_read(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Отметить все уведомления как прочитанные"""

    db.query(UserNotification).filter(
        UserNotification.user_id == current_user.id,
        UserNotification.is_read == False
    ).update({"is_read": True, "read_at": datetime.now()})

    db.commit()

    return {"success": True, "message": "All notifications marked as read"}


@router.post("/push-token")  
def register_push_token(
        token_data: PushTokenRegister,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Зарегистрировать push-токен устройства"""

    # TODO: сохранить токен в таблице устройств
    # Пока просто возвращаем успех

    return {
        "success": True,
        "message": f"Push token registered for {token_data.platform}"
    }