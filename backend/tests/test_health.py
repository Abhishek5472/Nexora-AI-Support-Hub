from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

# Dynamically add a test endpoint to test query parameter validation errors
@app.get("/test-validation-route")
def dummy_validation_endpoint(q: int):
    return {"q": q}

def test_general_health():
    """
    Asserts GET /api/v1/health returns general health details with Request-ID headers.
    """
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert "environment" in data
    assert "version" in data
    
    # Verify request ID presence in header
    assert "X-Request-ID" in response.headers
    assert len(response.headers["X-Request-ID"]) > 0

def test_database_health_unconfigured():
    """
    Asserts GET /api/v1/health/database returns status 200 and reports honest status.
    """
    response = client.get("/api/v1/health/database")
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert data["status"] in ["not_configured", "unavailable", "connected"]
    assert "X-Request-ID" in response.headers

def test_http_exception_response():
    """
    Asserts unmapped URL requests (404) trigger http exception handler returning normalized error response.
    """
    response = client.get("/api/v1/non-existent-endpoint-xyz")
    assert response.status_code == 404
    
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "HTTP_ERROR"
    assert "message" in data["error"]
    assert "request_id" in data["error"]
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Request-ID"] == data["error"]["request_id"]

def test_validation_error_normalization():
    """
    Asserts sending an invalid type to the test endpoint triggers validation exception handler
    returning a normalized validation error payload.
    """
    response = client.get("/test-validation-route?q=invalid-string-value")
    assert response.status_code == 422
    
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "message" in data["error"]
    assert "request_id" in data["error"]
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Request-ID"] == data["error"]["request_id"]
    
    # Message should detail that "q" parameter validation failed
    assert "q" in data["error"]["message"]
