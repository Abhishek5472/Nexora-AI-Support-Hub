import time
import logging
from typing import Dict, List
import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer

from backend.core.config import settings
from backend.core.security import decode_token
from backend.services.user_service import user_service

logger = logging.getLogger(__name__)

# OAuth2 Scheme extractor for Bearer access token
# Set auto_error=False so we can manually return consistent Phase 1 structured errors
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login",
    auto_error=False
)

# ------------------------------------------------------------------------------
# 1. Slide Window In-Memory Rate Limiter (Abuse Protection)
# ------------------------------------------------------------------------------
class InMemoryRateLimiter:
    """
    Lightweight, sliding-window rate limiter per client IP in memory.
    Requires no external dependencies.
    """
    def __init__(self, requests_limit: int, window_seconds: int):
        self.requests_limit = requests_limit
        self.window_seconds = window_seconds
        self.history: Dict[str, List[float]] = {}

    def __call__(self, request: Request) -> None:
        if settings.APP_ENV == "testing":
            return
        ip = request.client.host if request.client else "unknown-ip"
        now = time.time()

        if ip not in self.history:
            self.history[ip] = []

        # Prune expired timestamps outside the sliding window
        self.history[ip] = [t for t in self.history[ip] if now - t < self.window_seconds]

        # Verify limit
        if len(self.history[ip]) >= self.requests_limit:
            logger.warning(f"Rate limit triggered for IP {ip} on auth endpoints.")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many authentication requests. Please try again later."
            )

        self.history[ip].append(now)

# Limit auth registration/logins to 10 attempts per minute per IP
auth_rate_limiter = InMemoryRateLimiter(requests_limit=10, window_seconds=60)

# ------------------------------------------------------------------------------
# 2. Authentication and Authorization Injectors
# ------------------------------------------------------------------------------
async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Dependency that extracts the Bearer token, decodes JWT access claims,
    and resolves the authenticated active user from MongoDB.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or session has expired.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exception

    try:
        # Decode and enforce token type 'access'
        payload = decode_token(token, "access")
        user_id = payload.get("sub")
        if not user_id:
            raise credentials_exception
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError) as e:
        logger.warning(f"Token decoding failed in dependency verification: {e}")
        raise credentials_exception

    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise credentials_exception

    # Enforce active account status
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated. Please contact support."
        )

    return user

async def require_admin_role(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Dependency that verifies the currently authenticated user is an 'admin'.
    """
    if current_user.get("role") != "admin":
        logger.warning(f"User {current_user.get('email')} attempted access to restricted admin action.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. You do not have permissions to perform this action."
        )
    return current_user
