from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_admin_verification_flow(mock_db_isolation):
    """
    Verifies that RBAC blocks customer tokens while authorizing admin tokens
    on GET /api/v1/admin/verify.
    """
    # 1. Register a standard customer user
    email_cust = "customer_role@nexora.com"
    client.post("/api/v1/auth/register", json={
        "email": email_cust,
        "full_name": "Customer User",
        "password": "SecurePassword123!",
        "preferred_language": "en"
    })

    # 2. Register an admin-to-be user
    email_admin = "admin_role@nexora.com"
    client.post("/api/v1/auth/register", json={
        "email": email_admin,
        "full_name": "Admin User",
        "password": "SecurePassword123!",
        "preferred_language": "en"
    })

    # Promote the second user manually in the isolated mock database
    promoted = False
    for doc in mock_db_isolation.users.docs:
        if doc["email"] == email_admin:
            doc["role"] = "admin"
            promoted = True
            break
    assert promoted is True

    # 3. Authenticate both users
    res_cust = client.post("/api/v1/auth/login", json={
        "email": email_cust,
        "password": "SecurePassword123!"
    })
    token_cust = res_cust.json()["access_token"]

    res_admin = client.post("/api/v1/auth/login", json={
        "email": email_admin,
        "password": "SecurePassword123!"
    })
    token_admin = res_admin.json()["access_token"]

    # 4. Standard Customer attempts access (must return 403 Forbidden)
    response_cust = client.get(
        "/api/v1/admin/verify",
        headers={"Authorization": f"Bearer {token_cust}"}
    )
    assert response_cust.status_code == 403
    assert "Access denied" in response_cust.json()["error"]["message"]

    # 5. Admin attempts access (must return 200 OK)
    response_admin = client.get(
        "/api/v1/admin/verify",
        headers={"Authorization": f"Bearer {token_admin}"}
    )
    assert response_admin.status_code == 200
    
    data = response_admin.json()
    assert data["status"] == "verified"
    assert data["role"] == "admin"
    assert data["email"] == email_admin
