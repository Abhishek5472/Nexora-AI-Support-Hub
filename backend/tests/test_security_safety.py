import pytest
from unittest.mock import patch
from backend.core.config import settings
from backend.core.security import check_jwt_secret_safety

def test_check_jwt_secret_safety_missing():
    """
    Verifies that missing or empty JWT secrets are rejected with RuntimeError.
    """
    with patch.object(settings, "JWT_SECRET_KEY", None), \
         patch.object(settings, "APP_ENV", "production"):
        with pytest.raises(RuntimeError, match="missing"):
            check_jwt_secret_safety()

    with patch.object(settings, "JWT_SECRET_KEY", ""), \
         patch.object(settings, "APP_ENV", "production"):
        with pytest.raises(RuntimeError, match="missing"):
            check_jwt_secret_safety()

def test_check_jwt_secret_safety_too_short():
    """
    Verifies that keys shorter than 32 characters are rejected.
    """
    with patch.object(settings, "JWT_SECRET_KEY", "short_key_under_32_chars"), \
         patch.object(settings, "APP_ENV", "production"):
        with pytest.raises(RuntimeError, match="insecure"):
            check_jwt_secret_safety()

def test_check_jwt_secret_safety_exact_placeholder():
    """
    Verifies that default/placeholder strings are rejected.
    """
    with patch.object(settings, "JWT_SECRET_KEY", "placeholder_for_local_development_change_me_must_be_32_characters_long"), \
         patch.object(settings, "APP_ENV", "production"):
        with pytest.raises(RuntimeError, match="insecure"):
            check_jwt_secret_safety()

def test_check_jwt_secret_safety_obvious_prefix():
    """
    Verifies that obvios template prefixes like change-me or replace-me are rejected.
    """
    with patch.object(settings, "JWT_SECRET_KEY", "change-me-later-with-a-longer-key-string"), \
         patch.object(settings, "APP_ENV", "production"):
        with pytest.raises(RuntimeError, match="insecure"):
            check_jwt_secret_safety()

def test_check_jwt_secret_safety_strong_token():
    """
    Verifies that a strong high-entropy key of at least 32 characters is accepted.
    """
    strong_secret = "a" * 32
    with patch.object(settings, "JWT_SECRET_KEY", strong_secret), \
         patch.object(settings, "APP_ENV", "production"):
        # Must pass without raising exception
        check_jwt_secret_safety()

def test_check_jwt_secret_safety_strong_token_incidental_substring():
    """
    Verifies that strong keys containing incidental substrings like 'change' or 'secret'
    are NOT falsely rejected, avoiding false-positives.
    """
    incidental_secret = "my_strong_key_containing_incidental_secret_and_change_123!"
    assert len(incidental_secret) >= 32
    with patch.object(settings, "JWT_SECRET_KEY", incidental_secret), \
         patch.object(settings, "APP_ENV", "production"):
        # Must pass without raising exception
        check_jwt_secret_safety()
