import logging
from fastapi import APIRouter, Depends, HTTPException, status
from backend.core.dependencies import get_current_user
from backend.schemas.user import UserResponse, UserUpdate
from backend.services.user_service import user_service

logger = logging.getLogger(__name__)
router = APIRouter()

@router.patch("/me", response_model=UserResponse)
async def update_profile(
    profile_in: UserUpdate, 
    current_user: dict = Depends(get_current_user)
):
    """
    Updates the authenticated user's profile information.
    Only allows modifications to full_name and preferred_language.
    """
    user_id = str(current_user["_id"])
    updated_user = await user_service.update_user_profile(user_id, profile_in)
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update profile. Please check request body."
        )

    logger.info(f"Updated profile for user: {current_user.get('email')}")
    return updated_user
