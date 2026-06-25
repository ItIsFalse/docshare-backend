from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse
import os

from app.core.config import settings
from app.core.database import init_db
from app.api.v1 import (
    auth_router,
    users_router,
    roles_router,
    dashboard_router,
    vitals_router,
    appointments_router,
    family_router,
    activities_router,
    documents_router,
    doctor_router,
    admin_router,
    notifications_router,
    symptoms_router,
    environment_router,
    devices_router,
    doctors_router,
)

# Инициализация БД при старте
init_db()

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="DocShare - National Health Platform API"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Добавляем middleware для автоматического добавления слеша
class AddSlashMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Пропускаем специальные пути
        skip_paths = ["/", "/health", "/docs", "/openapi.json", "/redoc"]
        if path.startswith("/uploads"):
            return await call_next(request)
        if path in skip_paths:
            return await call_next(request)
        if "." in path.split("/")[-1]:
            return await call_next(request)

        # Если путь не заканчивается на "/" — добавляем
        if not path.endswith("/"):
            new_url = request.url.replace(path=path + "/")
            return RedirectResponse(new_url, status_code=307)

        return await call_next(request)

app.add_middleware(AddSlashMiddleware)

# Подключаем статические файлы
if os.path.exists("uploads"):
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Подключаем роутеры
app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(roles_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(vitals_router, prefix="/api/v1")
app.include_router(appointments_router, prefix="/api/v1")
app.include_router(family_router, prefix="/api/v1")
app.include_router(activities_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")
app.include_router(doctor_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(notifications_router, prefix="/api/v1")
app.include_router(symptoms_router, prefix="/api/v1")
app.include_router(environment_router, prefix="/api/v1")
app.include_router(devices_router, prefix="/api/v1")
app.include_router(doctors_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "status": "running",
        "version": "0.1.0"
    }

@app.get("/health")
async def health_check():
    return {"status": "ok"}