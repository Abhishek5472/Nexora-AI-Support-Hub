from fastapi import APIRouter
from backend.schemas.health import HealthResponse, DatabaseHealthResponse
from backend.database.connection import db_manager
from backend.core.config import settings

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
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

@router.get("/health/database", response_model=DatabaseHealthResponse)
async def get_database_health():
    """
    Checks and reports the connection status of the MongoDB database.
    Does not crash or return credentials/stack traces if unavailable.
    """
    status = await db_manager.check_health()
    return {"status": status}
