from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class KnowledgeSearchRequest(BaseModel):
    """
    Pydantic request validator for knowledge base similarity searches.
    """
    query: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="The semantic query string to search for in the company knowledge base."
    )
    top_k: int = Field(
        5,
        ge=1,
        le=20,
        description="The maximum number of relevant documents to retrieve."
    )

class KnowledgeSearchResult(BaseModel):
    """
    Pydantic schema representing a single retrieved text chunk match.
    """
    chunk_id: str
    text: str
    source_filename: str
    document_title: str
    page_start: int
    page_end: int
    similarity_score: float
    chunk_metadata: Optional[Dict[str, Any]] = None

class KnowledgeSearchResponse(BaseModel):
    """
    Pydantic response validator wrapping search query results.
    """
    query: str
    results: List[KnowledgeSearchResult]
