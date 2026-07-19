import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from backend.core.dependencies import get_current_user
from backend.schemas.chat import (
    ConversationCreate,
    ConversationResponse,
    MessageResponse,
    MessageCreate
)
from backend.services.chat_service import chat_service

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    payload: ConversationCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Creates a new multi-turn conversation session. Enforces a 50 active chats limit.
    """
    return await chat_service.create_conversation(
        user_id=str(current_user["_id"]),
        title=payload.title
    )

@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(
    current_user: dict = Depends(get_current_user)
):
    """
    Lists all chat sessions owned by the authenticated user.
    """
    return await chat_service.list_conversations(user_id=str(current_user["_id"]))

@router.get("/conversations/{id}", response_model=ConversationResponse)
async def get_conversation(
    id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Retrieves metadata of a single conversation session. Verifies ownership.
    """
    return await chat_service.verify_and_get_conversation(
        user_id=str(current_user["_id"]),
        conversation_id=id
    )

@router.delete("/conversations/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Deletes the conversation container and all its messages. Verifies ownership.
    """
    await chat_service.delete_conversation(
        user_id=str(current_user["_id"]),
        conversation_id=id
    )

@router.delete("/conversations/{id}/messages", status_code=status.HTTP_204_NO_CONTENT)
async def clear_conversation_messages(
    id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Clears all message histories belonging to the conversation. Verifies ownership.
    """
    await chat_service.clear_conversation_messages(
        user_id=str(current_user["_id"]),
        conversation_id=id
    )

@router.get("/conversations/{id}/messages", response_model=List[MessageResponse])
async def get_conversation_history(
    id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Fetches chronological message history for a conversation. Verifies ownership.
    """
    return await chat_service.get_conversation_messages(
        user_id=str(current_user["_id"]),
        conversation_id=id
    )

@router.post("/conversations/{id}/messages")
async def send_message(
    id: str,
    payload: MessageCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Submits a query, triggers FAISS semantic retrieval, and streams back the grounded
    response using Server-Sent Events (SSE). Verifies ownership.
    """
    # Quick ownership and validation pre-check
    await chat_service.verify_and_get_conversation(
        user_id=str(current_user["_id"]),
        conversation_id=id
    )
    
    return StreamingResponse(
        chat_service.stream_rag_response(
            user_id=str(current_user["_id"]),
            conversation_id=id,
            user_query=payload.content,
            regenerate_last=False
        ),
        media_type="text/event-stream"
    )

@router.post("/conversations/{id}/messages/regenerate")
async def regenerate_message(
    id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Aborts and removes the last assistant response, and regenerates a new response
    for the preceding user query. Verifies ownership.
    """
    # Fetch messages and extract last user query
    messages = await chat_service.get_conversation_messages(
        user_id=str(current_user["_id"]),
        conversation_id=id
    )
    user_queries = [m for m in messages if m["role"] == "user"]
    if not user_queries:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No user query exists in this conversation to regenerate response for."
        )
    last_query = user_queries[-1]["content"]

    return StreamingResponse(
        chat_service.stream_rag_response(
            user_id=str(current_user["_id"]),
            conversation_id=id,
            user_query=last_query,
            regenerate_last=True
        ),
        media_type="text/event-stream"
    )
