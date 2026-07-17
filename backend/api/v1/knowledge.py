import logging
from fastapi import APIRouter, Depends, HTTPException, status

from backend.core.dependencies import get_current_user
from backend.schemas.knowledge import KnowledgeSearchRequest, KnowledgeSearchResponse
from backend.services.rag_service import rag_service

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/search", response_model=KnowledgeSearchResponse, status_code=status.HTTP_200_OK)
async def search_knowledge_base(
    request: KnowledgeSearchRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Performs a semantic similarity search across the local FAISS vector index.
    Requires an authenticated active user session.
    """
    try:
        results = rag_service.query_similarity(
            query=request.query,
            top_k=request.top_k
        )
        return {
            "query": request.query,
            "results": results
        }
    except FileNotFoundError as e:
        logger.error(f"Vector store files are missing: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The knowledge base index is not initialized. Please build the index."
        )
    except ValueError as e:
        logger.warning(f"Validation failure during semantic search: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected failure during RAG search: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while querying the knowledge base. Please try again."
        )
