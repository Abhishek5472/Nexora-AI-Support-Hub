import logging
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from backend.core.config import settings
from backend.core.dependencies import auth_rate_limiter, get_current_user
from backend.schemas.auth import Token, UserLogin
from backend.schemas.user import UserCreate, UserResponse
from backend.services.user_service import user_service
from backend.services.session_service import session_service
from backend.services.auth_service import auth_service

logger = logging.getLogger(__name__)
router = APIRouter()

def set_refresh_cookie(response: Response, refresh_token: str) -> None:
    """
    Helper to set the secure HTTP-only refresh token cookie.
    """
    response.set_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        # Restricts cookie scope only to path matching auth refresh and logout endpoints
        path=f"{settings.API_V1_PREFIX}/auth",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    )

def clear_refresh_cookie(response: Response) -> None:
    """
    Helper to clear the refresh token cookie with identical configurations.
    """
    response.delete_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        path=f"{settings.API_V1_PREFIX}/auth",
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE
    )

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, _=Depends(auth_rate_limiter)):
    """
    Registers a new user profile as a customer. Checks password strength and duplicate emails.
    """
    user = await user_service.create_user(user_in)
    return user

@router.post("/login", response_model=Token)
async def login(response: Response, credentials: UserLogin, _=Depends(auth_rate_limiter)):
    """
    Logs in a user, issues short-lived JWT access token, and sets the HTTP-only refresh token cookie.
    """
    user = await auth_service.authenticate_user(credentials.email, credentials.password)
    
    access_token, refresh_token = await auth_service.create_auth_session(
        user_id=str(user["_id"]),
        role=user["role"]
    )

    set_refresh_cookie(response, refresh_token)
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/refresh", response_model=Token)
async def refresh(request: Request, response: Response):
    """
    Validates the refresh token cookie, rotates it, sets new cookie, and returns a new access token.
    """
    old_refresh_token = request.cookies.get(settings.REFRESH_COOKIE_NAME)
    if not old_refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is missing. Please log in."
        )

    access_token, new_refresh_token = await auth_service.rotate_refresh_session(old_refresh_token)
    set_refresh_cookie(response, new_refresh_token)
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout")
async def logout(request: Request, response: Response):
    """
    Revokes the current refresh session and clears the refresh token cookie.
    """
    refresh_token = request.cookies.get(settings.REFRESH_COOKIE_NAME)
    if refresh_token:
        # Revoke the session hash in MongoDB
        await session_service.revoke_session(refresh_token)

    clear_refresh_cookie(response)
    return {"message": "Successfully logged out from current session."}

@router.post("/logout-all")
async def logout_all(response: Response, current_user: dict = Depends(get_current_user)):
    """
    Revokes all active sessions for the current user and clears cookies.
    """
    user_id = str(current_user["_id"])
    await session_service.revoke_all_user_sessions(user_id)
    clear_refresh_cookie(response)
    return {"message": "Successfully logged out from all sessions/devices."}

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    Returns the currently authenticated user profile.
    """
    return current_user
