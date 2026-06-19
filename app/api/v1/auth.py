from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import secrets
import httpx

from ...core.database import get_db
from ...core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token
)
from ...core.dependencies import get_current_user
from ...models.user import User
from ...models.refresh_token import RefreshToken
from ...schemas.auth import (
    UserRegister, UserLogin, TokenResponse,
    UserResponse, RefreshTokenRequest,
    ForgotPasswordRequest, ResetPasswordRequest,
    GoogleLogin
)
from ...services.email_service import send_reset_email

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Регистрация нового пользователя"""
    # Проверяем, существует ли email
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Создаем пользователя
    hashed_password = hash_password(user_data.password)
    new_user = User(
        email=user_data.email,
        password_hash=hashed_password,
        full_name=user_data.full_name,
        phone=user_data.phone,
        city=user_data.city,
        role="citizen",  # По умолчанию
        auth_provider="email"
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Создаем токены
    access_token = create_access_token({"sub": str(new_user.id)})
    refresh_token = create_refresh_token({"sub": str(new_user.id)})

    # Сохраняем refresh token
    db_refresh = RefreshToken(
        user_id=new_user.id,
        token=refresh_token,
        expires_at=datetime.utcnow() + timedelta(days=7)
    )
    db.add(db_refresh)
    db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/login", response_model=TokenResponse)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """Вход в систему"""
    user = db.query(User).filter(User.email == user_data.email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    if not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account uses Google login. Please use Google."
        )

    if not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is blocked"
        )

    # Обновляем last_login
    user.last_login = datetime.utcnow()
    db.commit()

    # Создаем токены
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    # Сохраняем refresh token
    db_refresh = RefreshToken(
        user_id=user.id,
        token=refresh_token,
        expires_at=datetime.utcnow() + timedelta(days=7)
    )
    db.add(db_refresh)
    db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Обновление access токена"""
    # Проверяем refresh token
    token_data = decode_token(request.refresh_token)

    if token_data.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )

    # Проверяем в БД
    db_token = db.query(RefreshToken).filter(
        RefreshToken.token == request.refresh_token,
        RefreshToken.revoked_at.is_(None)
    ).first()

    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    # Создаем новые токены
    user_id = token_data.get("sub")
    access_token = create_access_token({"sub": user_id})
    refresh_token = create_refresh_token({"sub": user_id})

    # Обновляем refresh token
    db_token.token = refresh_token
    db_token.expires_at = datetime.utcnow() + timedelta(days=7)
    db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/logout")
def logout(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Выход из системы (отзыв refresh токена)"""
    db_token = db.query(RefreshToken).filter(
        RefreshToken.token == request.refresh_token
    ).first()

    if db_token:
        db_token.revoked_at = datetime.utcnow()
        db.commit()

    return {"success": True, "message": "Logged out"}


@router.post("/google", response_model=TokenResponse)
def google_login(google_data: GoogleLogin, db: Session = Depends(get_db)):
    """Вход через Google OAuth"""
    # TODO: Реализовать проверку Google ID токена
    # Пока заглушка

    # Временно создаем пользователя
    # Должна быть реализация с верификацией через Google API

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Google login not implemented yet"
    )


@router.post("/forgot-password")
def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Запрос на восстановление пароля"""
    user = db.query(User).filter(User.email == request.email).first()

    if not user:
        # Не показываем, что пользователь не найден (безопасность)
        return {"success": True, "message": "If email exists, reset code sent"}

    # Генерируем код
    reset_code = secrets.token_urlsafe(32)

    # Сохраняем в БД (можно в отдельной таблице или в пользователе)
    # Пока просто отправляем email

    # Отправка email
    send_reset_email(user.email, reset_code)

    return {"success": True, "message": "Reset code sent to your email"}


@router.post("/reset-password")
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Сброс пароля"""
    # TODO: Проверка токена из email

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Password reset not implemented yet"
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Получение текущего пользователя"""
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