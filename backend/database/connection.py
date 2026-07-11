import logging
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from backend.core.config import settings

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Manages the lifecycle of the MongoDB connection using the Motor async driver.
    """
    def __init__(self):
        self.client: AsyncIOMotorClient | None = None
        self.db = None

    async def connect(self) -> None:
        """
        Initializes the MongoDB client on startup.
        Fails gracefully if credentials are not configured or connection is lost.
        """
        if not settings.MONGODB_URI:
            logger.warning("MONGODB_URI is not set. Database integration will be disabled.")
            return

        try:
            # Connect using the client; set a short timeout so application startup is not blocked
            self.client = AsyncIOMotorClient(
                settings.MONGODB_URI,
                serverSelectionTimeoutMS=2000,
                uuidRepresentation="standard"
            )
            self.db = self.client[settings.MONGODB_DATABASE]
            # Perform a test ping to verify connectivity
            await self.client.admin.command("ping")
            logger.info("Successfully established connection to MongoDB.")
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Could not connect to MongoDB on startup: {e}")
            # Do not raise the exception; let the app run with health check reporting unavailable

    async def close(self) -> None:
        """
        Closes the MongoDB client connection on shutdown.
        """
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed.")

    async def check_health(self) -> str:
        """
        Pings the database to determine its current status.
        Returns:
            - "connected" if successfully pinged
            - "unavailable" if connection failed
            - "not_configured" if URI is missing
        """
        if not settings.MONGODB_URI:
            return "not_configured"
        if not self.client:
            return "unavailable"
        
        try:
            # Send a ping command to admin database
            await self.client.admin.command("ping")
            return "connected"
        except Exception as e:
            logger.warning(f"Database health check failed: {e}")
            return "unavailable"

# Global database manager instance
db_manager = DatabaseManager()
