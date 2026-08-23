from fastapi import APIRouter

from app.api.admin_auth import router as admin_auth_router
from app.api.admin_candidates import router as admin_candidates_router
from app.api.admin_content import router as admin_content_router
from app.api.health import router as health_router
from app.api.public_content import router as public_content_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(admin_auth_router)
api_router.include_router(admin_candidates_router)
api_router.include_router(admin_content_router)
api_router.include_router(public_content_router)
