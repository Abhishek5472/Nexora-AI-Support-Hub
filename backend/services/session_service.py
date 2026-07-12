import hashlib
import logging
from datetime import datetime, timezone
from bson import ObjectId
from backend.database.connection import db_manager

logger = logging.getLogger(__name__)

def hash_token(token: str) -> str:
    """
    Computes a SHA-256 hash of a string token to avoid storing plaintext in database.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

class SessionService:
    """
    Service class handling operations related to customer refresh token sessions in MongoDB.
    """
    async def create_session(self, user_id: str, refresh_token: str, expires_at: int) -> dict:
        """
        Creates and stores a hashed, revocable session document in MongoDB.
        """
        if db_manager.db is None:
            raise RuntimeError("Database connection is not initialized.")

        token_hash = hash_token(refresh_token)
        now = datetime.now(timezone.utc)
        
        # MongoDB TTL index requires BSON datetime (timezone-aware)
        expires_at_dt = datetime.fromtimestamp(expires_at, tz=timezone.utc)

        session_doc = {
            "user_id": ObjectId(user_id),
            "refresh_token_hash": token_hash,
            "created_at": now,
            "expires_at": expires_at_dt,
            "last_used_at": now,
            "is_revoked": False,
            "revoked_at": None
        }

        await db_manager.db.sessions.insert_one(session_doc)
        logger.debug(f"Created new session in MongoDB for user: {user_id}")
        return session_doc

    async def rotate_session(self, old_refresh_token: str, new_refresh_token: str, new_expires_at: int) -> ObjectId | None:
        """
        Atomically rotates a session: revokes the old session (if not already revoked)
        and creates a new session document for the rotated token.
        Ensures atomicity to prevent double-valid sessions.
        """
        if db_manager.db is None:
            return None

        old_hash = hash_token(old_refresh_token)
        now = datetime.now(timezone.utc)

        # 1. Atomically query and revoke the old session
        old_session = await db_manager.db.sessions.find_one_and_update(
            {
                "refresh_token_hash": old_hash,
                "is_revoked": False
            },
            {
                "$set": {
                    "is_revoked": True,
                    "revoked_at": now
                }
            },
            return_document=True
        )

        if not old_session:
            logger.warning("Attempted token rotation with a reused, revoked, or non-existent session.")
            return None

        # Verify old session hasn't expired yet
        if old_session["expires_at"].replace(tzinfo=timezone.utc) < now:
            logger.warning("Attempted token rotation on an expired session.")
            return None

        user_id = str(old_session["user_id"])
        
        # 2. Create the new session
        await self.create_session(
            user_id=user_id,
            refresh_token=new_refresh_token,
            expires_at=new_expires_at
        )

        return old_session["user_id"]

    async def revoke_session(self, refresh_token: str) -> bool:
        """
        Revokes a single session by token hash.
        """
        if db_manager.db is None:
            return False

        token_hash = hash_token(refresh_token)
        now = datetime.now(timezone.utc)

        result = await db_manager.db.sessions.update_one(
            {"refresh_token_hash": token_hash, "is_revoked": False},
            {"$set": {"is_revoked": True, "revoked_at": now}}
        )

        return result.modified_count > 0

    async def revoke_all_user_sessions(self, user_id: str) -> int:
        """
        Revokes all active sessions belonging to the user.
        """
        if db_manager.db is None:
            return 0

        now = datetime.now(timezone.utc)
        result = await db_manager.db.sessions.update_many(
            {"user_id": ObjectId(user_id), "is_revoked": False},
            {"$set": {"is_revoked": True, "revoked_at": now}}
        )

        logger.info(f"Revoked {result.modified_count} sessions for user: {user_id}")
        return result.modified_count

# Global SessionService instance
session_service = SessionService()
