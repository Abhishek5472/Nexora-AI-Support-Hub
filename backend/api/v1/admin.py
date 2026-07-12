from fastapi import APIRouter, Depends
from backend.core.dependencies import require_admin_role

router = APIRouter()

@router.get("/verify")
async def verify_admin(current_user: dict = Depends(require_admin_role)):
    """
    Verifies that the user is authenticated and possesses the 'admin' role.
    """
    return {
        "status": "verified",
        "role": "admin",
        "email": current_user.get("email"),
        "full_name": current_user.get("full_name")
    }
