from pydantic import BaseModel, Field

class UserLogin(BaseModel):
    """
    Pydantic schema representing credentials required for customer login.
    """
    email: str = Field(..., description="The user's registered email address")
    password: str = Field(..., description="The user's password")

class Token(BaseModel):
    """
    Pydantic schema representing the Access Token payload returned upon login.
    """
    access_token: str
    token_type: str = "bearer"
