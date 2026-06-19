from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from ..core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)  # NULL для Google OAuth

    full_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    city = Column(String(100), nullable=True)

    # Auth
    auth_provider = Column(String(50), default="email")  # email | google
    provider_id = Column(String(255), nullable=True)  # Google ID

    # Role
    role = Column(String(50), default="citizen")  # citizen, doctor, regional_admin, national_admin

    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime, nullable=True)