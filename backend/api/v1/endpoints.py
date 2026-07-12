from fastapi import APIRouter
from backend.schemas.health import HealthResponse, DatabaseHealthResponse
from backend.database.connection import db_manager
from backend.core.config import settings
from backend.api.v1.auth import router as auth_router
from backend.api.v1.users import router as users_router
from backend.api.v1.admin import router as admin_router

router = APIRouter()

# Mount new Phase 2 endpoint routers
router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
router.include_router(users_router, prefix="/users", tags=["User Profile"])
router.include_router(admin_router, prefix="/admin", tags=["Admin/RBAC"])

@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def get_general_health():
    """
    Returns general system health information, including configuration environment.
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "version": "0.1.0"
    }

@router.get("/health/database", response_model=DatabaseHealthResponse, tags=["Health"])
async def get_database_health():
    """
    Checks and reports the connection status of the MongoDB database.
    Does not crash or return credentials/stack traces if unavailable.
    """
    status = await db_manager.check_health()
    return {"status": status}
