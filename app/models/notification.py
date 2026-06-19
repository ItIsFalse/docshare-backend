from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, JSON, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..core.database import Base


class NotificationTemplate(Base):
    __tablename__ = "notification_templates"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False)
    type = Column(String(50), nullable=False)
    title_uz = Column(String(255), nullable=False)
    title_ru = Column(String(255), nullable=False)
    title_eu = Column(String(255), nullable=False)
    params_schema = Column(JSON, nullable=True)
    priority = Column(String(20), default="normal")
    is_active = Column(Boolean, default=True)


class UserNotification(Base):
    __tablename__ = "user_notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    template_id = Column(Integer, ForeignKey("notification_templates.id"), nullable=False)

    params = Column(JSON, nullable=True)
    related_type = Column(String(50), nullable=True)  # appointment, family_invitation, etc.
    related_id = Column(Integer, nullable=True)

    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)
    is_sent_push = Column(Boolean, default=False)
    is_sent_email = Column(Boolean, default=False)

    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    user = relationship("User", backref="notifications")
    template = relationship("NotificationTemplate", backref="notifications")