import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from backend.core.config import settings

# Initialize Argon2 Password Hasher
_hasher = PasswordHasher()

def check_jwt_secret_safety() -> None:
    """
    Validates that JWT_SECRET_KEY is configured securely.
    Fails startup with RuntimeError if key is missing, default/placeholder, or too short.
    Allows fallback in testing environment.
    """
    secret = settings.JWT_SECRET_KEY
    if not secret:
        raise RuntimeError("JWT_SECRET_KEY environment variable is missing!")

    secret_norm = secret.strip().lower()

    # Exact known unsafe placeholder or example values to reject
    rejected_exact = {
        "placeholder_for_local_development_change_me_must_be_32_characters_long",
        "placeholder_for_local_development",
        "changeme",
        "change_me",
        "replace_me",
        "replaceme",
        "your_secret",
        "yoursecret",
        "example_secret",
        "examplesecret",
        "secret",
        "placeholder",
    }

    # Obvious prefixes of unsafe templates to reject
    rejected_prefixes = (
        "change-me",
        "change_me",
        "changeme",
        "replace-me",
        "replace_me",
        "replaceme",
        "your-secret",
        "your_secret",
        "yoursecret",
        "example-secret",
        "example_secret",
        "examplesecret",
        "placeholder",
    )

    is_unsafe = (
        secret_norm in rejected_exact
        or secret_norm.startswith(rejected_prefixes)
    )

    if is_unsafe or len(secret) < 32:
        if settings.APP_ENV == "testing":
            return  # Allow insecure fallback key only in isolated tests
        raise RuntimeError(
            f"JWT_SECRET_KEY is insecure! It cannot contain placeholders and must be "
            f"at least 32 characters long. Current length: {len(secret)}. Please update "
            f"your root .env configuration."
        )

def hash_password(password: str) -> str:
    """
    Hashes a plaintext password using Argon2id.
    """
    return _hasher.hash(password)

def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verifies a plaintext password against an Argon2id hash.
    """
    try:
        return _hasher.verify(hashed_password, password)
    except VerifyMismatchError:
        return False

def validate_password_strength(password: str) -> str | None:
    """
    Validates password strength rules:
    - Minimum length of 8, max 128
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    Returns an error message string if invalid, or None if valid.
    """
    if len(password) < 8:
        return "Password must be at least 8 characters long."
    if len(password) > 128:
        return "Password must not exceed 128 characters."
    if not re.search(r"[A-Z]", password):
        return "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return "Password must contain at least one lowercase letter."
    if not re.search(r"\d", password):
        return "Password must contain at least one number."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return "Password must contain at least one special character."
    return None

def create_access_token(user_id: str, role: str) -> str:
    """
    Generates a short-lived access JWT token.
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    payload = {
        "sub": user_id,
        "role": role,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "jti": str(uuid.uuid4())
    }
    
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def create_refresh_token(user_id: str) -> str:
    """
    Generates a longer-lived refresh JWT token.
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    payload = {
        "sub": user_id,
        "type": "refresh",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "jti": str(uuid.uuid4())
    }
    
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def decode_token(token: str, expected_type: str) -> Dict[str, Any]:
    """
    Decodes a JWT and validates its type, signature, and expiration.
    Raises:
        jwt.ExpiredSignatureError: if expired
        jwt.InvalidTokenError: if invalid token/wrong type
    """
    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    if payload.get("type") != expected_type:
        raise jwt.InvalidTokenError(f"Invalid token type: expected {expected_type}")
    return payload
