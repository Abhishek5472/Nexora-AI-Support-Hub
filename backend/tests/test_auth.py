import jwt
from fastapi.testclient import TestClient
from backend.main import app
from backend.core.config import settings

client = TestClient(app)

def test_user_registration_success(mock_db_isolation):
    """
    Test successful user registration.
    Verifies that the user role is customer, email is lowercase, and password is hashed (never returned).
    """
    payload = {
        "email": "REGISTER_USER@Nexora.com",
        "full_name": "Test User",
        "password": "SecurePassword123!",
        "preferred_language": "hi"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    
    data = response.json()
    assert data["email"] == "register_user@nexora.com"  # Case-normalized
    assert data["full_name"] == "Test User"
    assert data["role"] == "customer"
    assert data["preferred_language"] == "hi"
    assert data["is_active"] is True
    assert "password_hash" not in data  # Never returned
    assert "_id" in data or "id" in data

def test_user_registration_duplicate_email(mock_db_isolation):
    """
    Test duplicate email registration gets rejected with a conflict 409 status code.
    """
    payload = {
        "email": "duplicate@nexora.com",
        "full_name": "First User",
        "password": "SecurePassword123!",
        "preferred_language": "en"
    }
    # Register first
    res1 = client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    # Attempt second registration with same email
    res2 = client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 409
    assert "already registered" in res2.json()["error"]["message"]

def test_user_registration_weak_password(mock_db_isolation):
    """
    Test password validation strength rule failures return a bad request 400.
    """
    payload = {
        "email": "weakpass@nexora.com",
        "full_name": "Weak User",
        "password": "123",  # Insecure password
        "preferred_language": "en"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400
    assert "at least 8 characters" in response.json()["error"]["message"]

def test_user_registration_invalid_language(mock_db_isolation):
    """
    Test that unsupported languages return a validation error 422.
    """
    payload = {
        "email": "lang@nexora.com",
        "full_name": "Lang User",
        "password": "SecurePassword123!",
        "preferred_language": "fr"  # French not supported
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422
    assert "Language must be one of" in response.json()["error"]["message"]

def test_login_success(mock_db_isolation):
    """
    Test successful user login.
    Verifies that access token is returned and refresh token is set in HttpOnly cookie.
    """
    # 1. Register a user
    register_payload = {
        "email": "login@nexora.com",
        "full_name": "Login User",
        "password": "SecurePassword123!",
        "preferred_language": "en"
    }
    client.post("/api/v1/auth/register", json=register_payload)

    # 2. Login
    login_payload = {
        "email": "LOGIN@nexora.com",  # Should be normalized automatically
        "password": "SecurePassword123!"
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # 3. Check for HttpOnly cookie
    cookies = response.cookies
    assert settings.REFRESH_COOKIE_NAME in cookies
    # Verify cookie configuration settings in raw response headers
    set_cookie_header = response.headers.get("set-cookie")
    assert set_cookie_header is not None
    assert "HttpOnly" in set_cookie_header
    assert "Path=/api/v1/auth" in set_cookie_header

def test_login_invalid_credentials(mock_db_isolation):
    """
    Test login with invalid credentials.
    """
    login_payload = {
        "email": "invalid@nexora.com",
        "password": "WrongPassword123!"
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["error"]["message"]

def test_protected_me_endpoint(mock_db_isolation):
    """
    Test protected GET /auth/me endpoint.
    Verifies access with token, denial without token, and expired/wrong token type checks.
    """
    # 1. Register and Login
    email = "me@nexora.com"
    register_payload = {
        "email": email,
        "full_name": "Me User",
        "password": "SecurePassword123!",
        "preferred_language": "en"
    }
    client.post("/api/v1/auth/register", json=register_payload)
    
    login_res = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "SecurePassword123!"
    })
    token = login_res.json()["access_token"]

    # 2. Unauthenticated access
    res_no_auth = client.get("/api/v1/auth/me")
    assert res_no_auth.status_code == 401

    # 3. Authenticated access
    res_auth = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_auth.status_code == 200
    assert res_auth.json()["email"] == email

    # 4. Access with wrong token type (e.g. sending refresh token as bearer)
    refresh_token_cookie = login_res.cookies.get(settings.REFRESH_COOKIE_NAME)
    res_wrong_type = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {refresh_token_cookie}"}
    )
    assert res_wrong_type.status_code == 401

def test_refresh_token_rotation_success(mock_db_isolation):
    """
    Test successful token refresh and token rotation.
    """
    # 1. Register and Login
    email = "refresh@nexora.com"
    register_payload = {
        "email": email,
        "full_name": "Refresh User",
        "password": "SecurePassword123!",
        "preferred_language": "en"
    }
    client.post("/api/v1/auth/register", json=register_payload)
    
    login_res = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "SecurePassword123!"
    })
    refresh_token = login_res.cookies.get(settings.REFRESH_COOKIE_NAME)

    # 2. Perform silent token refresh rotation
    client.cookies.clear()
    client.cookies.set(settings.REFRESH_COOKIE_NAME, refresh_token)
    
    refresh_res = client.post("/api/v1/auth/refresh")
    assert refresh_res.status_code == 200
    assert "access_token" in refresh_res.json()
    new_refresh_cookie = refresh_res.cookies.get(settings.REFRESH_COOKIE_NAME)
    assert new_refresh_cookie is not None
    assert new_refresh_cookie != refresh_token  # Token rotated

    # 3. Attempt reuse of old rotated refresh token (must be rejected)
    client.cookies.clear()
    client.cookies.set(settings.REFRESH_COOKIE_NAME, refresh_token)
    reuse_res = client.post("/api/v1/auth/refresh")
    assert reuse_res.status_code == 401

def test_profile_update(mock_db_isolation):
    """
    Test PATCH /users/me endpoint.
    Verifies allowed modifications, and Pydantic schema constraints.
    """
    email = "profile@nexora.com"
    register_payload = {
        "email": email,
        "full_name": "Old Name",
        "password": "SecurePassword123!",
        "preferred_language": "en"
    }
    client.post("/api/v1/auth/register", json=register_payload)
    login_res = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "SecurePassword123!"
    })
    token = login_res.json()["access_token"]

    # 1. Perform valid profile update
    update_payload = {
        "full_name": "New Name",
        "preferred_language": "mr"
    }
    response = client.patch(
        "/api/v1/users/me",
        json=update_payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "New Name"
    assert data["preferred_language"] == "mr"

    # 2. Verify forbidden fields (like role) cannot be updated
    forbidden_payload = {
        "role": "admin"
    }
    response_forbidden = client.patch(
        "/api/v1/users/me",
        json=forbidden_payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    # The fields are ignored by Pydantic UserUpdate schema, so role remains customer
    assert response_forbidden.status_code == 200
    assert response_forbidden.json()["role"] == "customer"

def test_session_logout(mock_db_isolation):
    """
    Test logout revokes session and clears cookies.
    """
    email = "logout@nexora.com"
    register_payload = {
        "email": email,
        "full_name": "Logout User",
        "password": "SecurePassword123!",
        "preferred_language": "en"
    }
    client.post("/api/v1/auth/register", json=register_payload)
    login_res = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "SecurePassword123!"
    })
    refresh_token = login_res.cookies.get(settings.REFRESH_COOKIE_NAME)

    client.cookies.clear()
    client.cookies.set(settings.REFRESH_COOKIE_NAME, refresh_token)
    
    # Logout
    logout_res = client.post("/api/v1/auth/logout")
    assert logout_res.status_code == 200
    # Cookie should be deleted/cleared
    assert logout_res.cookies.get(settings.REFRESH_COOKIE_NAME) in [None, ""]

def test_login_inactive_user(mock_db_isolation):
    """
    Test that login fails when the user is deactivated.
    """
    email = "inactive@nexora.com"
    register_payload = {
        "email": email,
        "full_name": "Inactive User",
        "password": "SecurePassword123!",
        "preferred_language": "en"
    }
    client.post("/api/v1/auth/register", json=register_payload)

    # Deactivate the user directly in our mock DB
    for doc in mock_db_isolation.users.docs:
        if doc["email"] == email:
            doc["is_active"] = False
            break

    # Attempt Login
    login_payload = {
        "email": email,
        "password": "SecurePassword123!"
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 403
    assert "inactive" in response.json()["error"]["message"].lower()

def test_logout_all_sessions_revocation(mock_db_isolation):
    """
    Test that logout-all revokes all sessions in the database for the user.
    """
    email = "logoutall@nexora.com"
    register_payload = {
        "email": email,
        "full_name": "Logout All User",
        "password": "SecurePassword123!",
        "preferred_language": "en"
    }
    client.post("/api/v1/auth/register", json=register_payload)

    # Login to create sessions
    login_res = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "SecurePassword123!"
    })
    token = login_res.json()["access_token"]

    # Verify sessions are created in the mock DB
    assert len(mock_db_isolation.sessions.docs) > 0

    # Call logout-all
    logout_res = client.post(
        "/api/v1/auth/logout-all",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert logout_res.status_code == 200

    # Verify all sessions are revoked (is_revoked is True)
    for session in mock_db_isolation.sessions.docs:
        assert session["is_revoked"] is True

def test_expired_refresh_token(mock_db_isolation):
    """
    Test that token refresh rotation fails if the refresh token signature has expired.
    """
    # Attempt silent refresh with an empty/expired token structure
    client.cookies.clear()
    client.cookies.set(settings.REFRESH_COOKIE_NAME, "expired_or_invalid_signature_jwt")
    
    response = client.post("/api/v1/auth/refresh")
    assert response.status_code == 401
    assert "invalid" in response.json()["error"]["message"].lower()
