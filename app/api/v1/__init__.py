from .auth import router as auth_router
from .users import router as users_router
from .roles import router as roles_router
from .dashboard import router as dashboard_router
from .vitals import router as vitals_router
from .appointments import router as appointments_router
from .family import router as family_router
from .activities import router as activities_router
from .documents import router as documents_router
from .doctor import router as doctor_router
from .admin import router as admin_router
from .notifications import router as notifications_router
from .symptoms import router as symptoms_router
from .environment import router as environment_router
from .devices import router as devices_router
from .doctors import router as doctors_router

__all__ = [
    "auth_router",
    "users_router",
    "roles_router",
    "dashboard_router",
    "vitals_router",
    "appointments_router",
    "family_router",
    "activities_router",
    "documents_router",
    "doctor_router",
    "admin_router",
    "notifications_router",
    "symptoms_router",
    "environment_router",
    "devices_router",
    "doctors_router",
]