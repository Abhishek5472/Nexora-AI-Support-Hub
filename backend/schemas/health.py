from pydantic import BaseModel, Field

class HealthResponse(BaseModel):
    """
    Pydantic schema representing the general health check response.
    """
    status: str = Field(..., json_schema_extra={"example": "healthy"})
    service: str = Field(..., json_schema_extra={"example": "Nexora AI Support Hub API"})
    environment: str = Field(..., json_schema_extra={"example": "development"})
    version: str = Field(..., json_schema_extra={"example": "0.1.0"})

class DatabaseHealthResponse(BaseModel):
    """
    Pydantic schema representing the database health check response.
    """
    status: str = Field(
        ..., 
        json_schema_extra={"example": "connected"}, 
        description="Current MongoDB status: 'connected', 'unavailable', or 'not_configured'"
    )
