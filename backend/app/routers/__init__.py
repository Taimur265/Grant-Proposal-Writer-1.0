"""API routers."""

from app.routers.auth import router as auth_router
from app.routers.projects import router as projects_router
from app.routers.documents import router as documents_router
from app.routers.proposals import router as proposals_router

__all__ = [
    "auth_router",
    "projects_router",
    "documents_router",
    "proposals_router",
]
