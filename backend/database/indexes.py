import logging
from pymongo import ASCENDING
from backend.database.connection import db_manager

logger = logging.getLogger(__name__)

async def create_indexes() -> None:
    """
    Creates/verifies database indexes for users and sessions collections.
    This operation is idempotent and safe to run on startup.
    """
    if db_manager.db is None:
        logger.warning("Database connection is inactive. Skipping database indexing setup.")
        return

    try:
        # 1. Unique index on users(email)
        await db_manager.db.users.create_index(
            [("email", ASCENDING)],
            unique=True,
            name="unique_user_email"
        )
        logger.info("MongoDB unique index on users(email) verified/created successfully.")

        # 2. Lookup index on sessions(user_id)
        await db_manager.db.sessions.create_index(
            [("user_id", ASCENDING)],
            name="idx_session_user_id"
        )

        # 3. Unique index on sessions(refresh_token_hash)
        await db_manager.db.sessions.create_index(
            [("refresh_token_hash", ASCENDING)],
            unique=True,
            name="unique_session_refresh_hash"
        )

        # 4. TTL Index on sessions(expires_at)
        # expireAfterSeconds=0 triggers deletion at the exact timestamp specified in expires_at (BSON datetime)
        await db_manager.db.sessions.create_index(
            [("expires_at", ASCENDING)],
            expireAfterSeconds=0,
            name="ttl_session_expiry"
        )
        logger.info("MongoDB TTL and lookup indexes on sessions verified/created successfully.")

    except Exception as e:
        logger.error(f"Failed to verify/create database indexes: {e}", exc_info=True)
