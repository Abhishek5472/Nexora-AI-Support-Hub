import logging
from datetime import datetime, timezone
from bson import ObjectId
from fastapi import HTTPException, status
from backend.database.connection import db_manager
from backend.schemas.user import UserCreate, UserUpdate
from backend.core.security import hash_password, validate_password_strength

logger = logging.getLogger(__name__)

class UserService:
    """
    Service class handling operations related to User CRUD and management.
    """
    async def get_user_by_email(self, email: str) -> dict | None:
        """
        Retrieves a user document by email (normalizing it to lowercase).
        """
        if db_manager.db is None:
            return None
        email_clean = email.strip().lower()
        return await db_manager.db.users.find_one({"email": email_clean})

    async def get_user_by_id(self, user_id: str) -> dict | None:
        """
        Retrieves a user document by its MongoDB ObjectId.
        """
        if db_manager.db is None:
            return None
        try:
            return await db_manager.db.users.find_one({"_id": ObjectId(user_id)})
        except Exception as e:
            logger.debug(f"Invalid user ID format: {user_id}. Error: {e}")
            return None

    async def create_user(self, user_in: UserCreate) -> dict:
        """
        Registers a new user, hashes the password, and returns the new document.
        Always registers public users as 'customer'.
        """
        if db_manager.db is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
                detail="Database is currently unavailable."
            )

        email_clean = user_in.email.strip().lower()

        # 1. Enforce password strength rules
        password_err = validate_password_strength(user_in.password)
        if password_err:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=password_err
            )

        # 2. Check for duplicate emails
        existing_user = await self.get_user_by_email(email_clean)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email address is already registered."
            )

        now = datetime.now(timezone.utc)
        user_doc = {
            "email": email_clean,
            "full_name": user_in.full_name.strip(),
            "password_hash": hash_password(user_in.password),
            "role": "customer",  # Default and enforced public registration role
            "preferred_language": user_in.preferred_language,
            "is_active": True,
            "is_email_verified": False,
            "created_at": now,
            "updated_at": now,
            "last_login_at": None
        }

        result = await db_manager.db.users.insert_one(user_doc)
        user_doc["_id"] = result.inserted_id
        logger.info(f"Registered new user: {email_clean} with ID: {result.inserted_id}")
        return user_doc

    async def update_user_profile(self, user_id: str, profile_in: UserUpdate) -> dict | None:
        """
        Updates the profile info of the user, only allowing safe field updates.
        """
        if db_manager.db is None:
            return None

        update_data = {}
        if profile_in.full_name is not None:
            update_data["full_name"] = profile_in.full_name.strip()
        if profile_in.preferred_language is not None:
            update_data["preferred_language"] = profile_in.preferred_language

        if not update_data:
            return await self.get_user_by_id(user_id)

        now = datetime.now(timezone.utc)
        update_data["updated_at"] = now

        try:
            # Atomic update using find_one_and_update
            updated_user = await db_manager.db.users.find_one_and_update(
                {"_id": ObjectId(user_id)},
                {"$set": update_data},
                return_document=True
            )
            return updated_user
        except Exception as e:
            logger.error(f"Failed to update user profile {user_id}: {e}")
            return None

    async def update_last_login(self, user_id: str) -> None:
        """
        Updates the user's last_login_at timestamp.
        """
        if db_manager.db is None:
            return
        now = datetime.now(timezone.utc)
        try:
            await db_manager.db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"last_login_at": now}}
            )
        except Exception as e:
            logger.error(f"Failed to update last login for user {user_id}: {e}")

# Global UserService instance
user_service = UserService()
