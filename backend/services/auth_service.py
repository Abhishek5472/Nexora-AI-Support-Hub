import logging
import jwt
from fastapi import HTTPException, status
from backend.services.user_service import user_service
from backend.services.session_service import session_service
from backend.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token
)

logger = logging.getLogger(__name__)

class AuthService:
    """
    Service class orchestrating authentication pipelines (login, refresh, logout).
    """
    async def authenticate_user(self, email: str, password: str) -> dict:
        """
        Verifies login credentials and updates last login timestamp.
        """
        email_clean = email.strip().lower()
        user = await user_service.get_user_by_email(email_clean)
        
        # Generic safe error message for login failures
        invalid_cred_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

        if not user:
            raise invalid_cred_exception

        if not verify_password(password, user["password_hash"]):
            raise invalid_cred_exception

        if not user.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive. Please contact system support."
            )

        # Update last login timestamp asynchronously
        await user_service.update_last_login(str(user["_id"]))

        return user

    async def create_auth_session(self, user_id: str, role: str) -> tuple[str, str]:
        """
        Creates a new authentication session: generates JWT access & refresh tokens
        and records the session in MongoDB.
        """
        access_token = create_access_token(user_id, role)
        refresh_token = create_refresh_token(user_id)
        
        # Decode refresh token to get exp time for database persistence
        payload = decode_token(refresh_token, "refresh")
        expires_at = payload["exp"]

        await session_service.create_session(
            user_id=user_id,
            refresh_token=refresh_token,
            expires_at=expires_at
        )

        return access_token, refresh_token

    async def rotate_refresh_session(self, old_refresh_token: str) -> tuple[str, str]:
        """
        Rotates the refresh session: validates old token, revokes old session,
        generates a new access token + refresh token, and persists the new session.
        """
        invalid_session_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired or is invalid. Please log in again."
        )

        try:
            # 1. Decode and validate token signature & expiration
            payload = decode_token(old_refresh_token, "refresh")
            user_id = payload["sub"]
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError) as e:
            logger.warning(f"Invalid refresh token decoded during refresh: {e}")
            raise invalid_session_exception

        # 2. Retrieve user and verify active status
        user = await user_service.get_user_by_id(user_id)
        if not user or not user.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive or disabled."
            )

        # 3. Generate new tokens
        new_access_token = create_access_token(user_id, user["role"])
        new_refresh_token = create_refresh_token(user_id)
        new_payload = decode_token(new_refresh_token, "refresh")
        new_expires_at = new_payload["exp"]

        # 4. Perform atomic rotation in the database
        rotated_user_id = await session_service.rotate_session(
            old_refresh_token=old_refresh_token,
            new_refresh_token=new_refresh_token,
            new_expires_at=new_expires_at
        )

        if not rotated_user_id:
            raise invalid_session_exception

        return new_access_token, new_refresh_token

# Global AuthService instance
auth_service = AuthService()
