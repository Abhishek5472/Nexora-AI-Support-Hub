# ------------------------------------------------------------------------------
# Package PATH Injection for Root/Subfolder Deployment Compatibility
# ------------------------------------------------------------------------------
import sys
import os

# Dynamic package binding to support both root-level and subfolder-level runs (Railway/Local)
_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)

if "backend" not in sys.modules:
    if os.path.exists(os.path.join(_parent_dir, "backend")):
        if _parent_dir not in sys.path:
            sys.path.insert(0, _parent_dir)
    else:
        # On cloud platforms (e.g. Railway) where the build context is set to backend/
        # and current_dir contains no 'backend' folder. We dynamically synthesize 'backend' package.
        import types
        _backend_pkg = types.ModuleType("backend")
        _backend_pkg.__path__ = [_current_dir]
        sys.modules["backend"] = _backend_pkg
        
        if _current_dir not in sys.path:
            sys.path.insert(0, _current_dir)
# ------------------------------------------------------------------------------

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.core.config import settings
from backend.core.middleware import RequestIDMiddleware
from backend.database.connection import db_manager
from backend.api.v1.endpoints import router as api_v1_router

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
# Suppress noisy MongoDB/PyMongo driver debug logs during local operation
logging.getLogger("pymongo").setLevel(logging.WARNING)
logging.getLogger("motor").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages startup and shutdown lifecycles of the application.
    """
    logger.info("Starting up Nexora AI Support Hub Backend...")
    # Verify JWT secret configuration safety
    from backend.core.security import check_jwt_secret_safety
    check_jwt_secret_safety()
    # Initialize MongoDB connection
    await db_manager.connect()
    yield
    logger.info("Shutting down Nexora AI Support Hub Backend...")
    # Close MongoDB connection
    await db_manager.close()

# Initialize FastAPI App
app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API for Nexora AI Support Hub",
    version="0.1.0",
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# ------------------------------------------------------------------------------
# Middlewares
# ------------------------------------------------------------------------------

# 1. Custom Request-ID and Security Headers Middleware
app.add_middleware(RequestIDMiddleware)

# 2. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------------------
# Exception Handlers (Consistent, Safe Error Normalization)
# ------------------------------------------------------------------------------

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handles Pydantic validation errors. Normalizes errors and returns details safely.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    errors = exc.errors()
    # Build a clean validation error details string
    error_details = []
    for err in errors:
        loc = " -> ".join(str(l) for l in err.get("loc", []))
        msg = err.get("msg", "Invalid value")
        error_details.append(f"[{loc}]: {msg}")
    
    error_message = "Validation failed: " + "; ".join(error_details)
    logger.warning(f"Validation error for request {request_id}: {error_message}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": error_message,
                "request_id": request_id
            }
        },
        headers={"X-Request-ID": request_id}
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Handles standard HTTPExceptions from Starlette/FastAPI (including 404s).
    """
    request_id = getattr(request.state, "request_id", "unknown")
    logger.warning(f"HTTP exception ({exc.status_code}) for request {request_id}: {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": "HTTP_ERROR",
                "message": exc.detail,
                "request_id": request_id
            }
        },
        headers={"X-Request-ID": request_id}
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    Catch-all exception handler to intercept unhandled exceptions.
    Prevents leaking internal stack traces, paths, or variables.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(f"Unhandled exception occurred on request {request_id}: {exc}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred. Please contact support.",
                "request_id": request_id
            }
        },
        headers={"X-Request-ID": request_id}
    )

# ------------------------------------------------------------------------------
# Routes Setup
# ------------------------------------------------------------------------------

# Mount v1 router
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

@app.get("/")
async def root_redirect():
    """
    Simple landing redirecting developers to the Swagger Documentation.
    """
    return {
        "message": f"Welcome to {settings.APP_NAME}!",
        "docs_url": "/docs",
        "health_url": f"{settings.API_V1_PREFIX}/health"
    }
