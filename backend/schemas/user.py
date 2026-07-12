import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing_extensions import Annotated
from pydantic import BeforeValidator

# Custom Pydantic type to convert MongoDB ObjectId to string
PyObjectId = Annotated[str, BeforeValidator(str)]

def validate_email_string(email: str) -> str:
    """
    Helper function to validate and normalize email format.
    """
    email_clean = email.strip().lower()
    if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email_clean):
        raise ValueError("Invalid email address format.")
    return email_clean

class UserBase(BaseModel):
    email: str
    full_name: str
    preferred_language: str = "en"
    is_active: bool = True
    is_email_verified: bool = False

    @field_validator("email")
    @classmethod
    def check_email(cls, v: str) -> str:
        return validate_email_string(v)

class UserCreate(BaseModel):
    email: str
    full_name: str
    password: str
    preferred_language: str = "en"

    @field_validator("email")
    @classmethod
    def check_email(cls, v: str) -> str:
        return validate_email_string(v)

    @field_validator("preferred_language")
    @classmethod
    def check_language(cls, v: str) -> str:
        langs = ["en", "hi", "mr"]
        if v not in langs:
            raise ValueError(f"Language must be one of: {', '.join(langs)}")
        return v

class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    preferred_language: Optional[str] = None

    @field_validator("preferred_language")
    @classmethod
    def check_language(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        langs = ["en", "hi", "mr"]
        if v not in langs:
            raise ValueError(f"Language must be one of: {', '.join(langs)}")
        return v

class UserResponse(BaseModel):
    id: PyObjectId = Field(alias="_id")
    email: str
    full_name: str
    role: str
    preferred_language: str
    is_active: bool
    is_email_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={datetime: lambda v: v.isoformat()}
    )
