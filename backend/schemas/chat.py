from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class CitationSchema(BaseModel):
    """
    Pydantic schema representing a RAG source citation.
    """
    chunk_id: str
    source_filename: str
    document_title: str
    page_start: int
    page_end: int
    similarity_score: float

class MessageResponse(BaseModel):
    """
    Response schema for a single conversation message log.
    """
    id: str = Field(..., alias="_id")
    conversation_id: str
    role: str
    content: str
    timestamp: datetime
    citations: Optional[List[CitationSchema]] = []
    is_interrupted: Optional[bool] = False

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class MessageCreate(BaseModel):
    """
    Request schema to submit a new query to the chat.
    """
    content: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="The query content. Rejects empty strings and enforces a 500 character budget."
    )

class ConversationCreate(BaseModel):
    """
    Request schema to create a new chat session.
    """
    title: Optional[str] = Field(None, max_length=100, description="Optional title. Auto-generated if not set.")

class ConversationResponse(BaseModel):
    """
    Response schema for conversation metadata.
    """
    id: str = Field(..., alias="_id")
    user_id: str
    title: str
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }
