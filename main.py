from fastapi import FastAPI, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import os

from app.core.config import settings
from app.core.database import init_db
from app.api.v1 import (
    auth, users, roles, dashboard, vitals,
    appointments, family, activities, documents,
    doctor, admin, notifications, symptoms, environment, devices
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
        if "." in path.split("/")[-1]:  # файлы с расширением
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
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(roles.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(vitals.router, prefix="/api/v1")
app.include_router(appointments.router, prefix="/api/v1")
app.include_router(family.router, prefix="/api/v1")
app.include_router(activities.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(doctor.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(notifications.router, prefix="/api/v1")
app.include_router(symptoms.router, prefix="/api/v1")
app.include_router(environment.router, prefix="/api/v1")
app.include_router(devices.router, prefix="/api/v1")


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

@app.get("/api/v1/doctors")
async def doctors_redirect():
    return RedirectResponse(url="/api/v1/appointments/doctors/")

@app.get("/api/v1/doctors/")
async def doctors_redirect_slash():
    return RedirectResponse(url="/api/v1/appointments/doctors/")