from .auth import router as auth_router
from .users import router as users_router
from .roles import router as roles_router
from .dashboard import router as dashboard_router
from .vitals import router as vitals_router
from .appointments import router as appointments_router
from .family import router as family_router
from .activities import router as activities_router
from .documents import router as documents_router

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
]