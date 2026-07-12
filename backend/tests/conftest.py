import copy
import pytest
from bson import ObjectId
from unittest.mock import MagicMock
from backend.database.connection import db_manager
from backend.core.config import settings

class MockCollection:
    """
    Mock class simulating a MongoDB collection in memory.
    Supports basic CRUD, queries, sets, and atomic updates.
    """
    def __init__(self, name: str):
        self.name = name
        self.docs = []

    async def find_one(self, query: dict) -> dict | None:
        for doc in self.docs:
            if self._match(doc, query):
                return copy.deepcopy(doc)
        return None

    async def insert_one(self, doc: dict) -> MagicMock:
        new_doc = copy.deepcopy(doc)
        if "_id" not in new_doc:
            new_doc["_id"] = ObjectId()
        self.docs.append(new_doc)
        
        # Simulating returned insert status
        res = MagicMock()
        res.inserted_id = new_doc["_id"]
        return res

    async def update_one(self, query: dict, update: dict) -> MagicMock:
        modified = 0
        for doc in self.docs:
            if self._match(doc, query):
                self._apply_update(doc, update)
                modified = 1
                break
        res = MagicMock()
        res.modified_count = modified
        return res

    async def update_many(self, query: dict, update: dict) -> MagicMock:
        modified = 0
        for doc in self.docs:
            if self._match(doc, query):
                self._apply_update(doc, update)
                modified += 1
        res = MagicMock()
        res.modified_count = modified
        return res

    async def find_one_and_update(self, query: dict, update: dict, return_document=None) -> dict | None:
        for doc in self.docs:
            if self._match(doc, query):
                self._apply_update(doc, update)
                return copy.deepcopy(doc)
        return None

    async def create_index(self, keys, **kwargs) -> str:
        return "mock_index"

    def _match(self, doc: dict, query: dict) -> bool:
        for k, v in query.items():
            if k == "_id":
                if doc.get("_id") != v:
                    return False
            elif doc.get(k) != v:
                return False
        return True

    def _apply_update(self, doc: dict, update: dict) -> None:
        if "$set" in update:
            for k, v in update["$set"].items():
                doc[k] = v

class MockDatabase:
    """
    Mock database referencing user and session in-memory collections.
    """
    def __init__(self):
        self.users = MockCollection("users")
        self.sessions = MockCollection("sessions")

    def __getitem__(self, name: str) -> MockCollection:
        if name == "users":
            return self.users
        if name == "sessions":
            return self.sessions
        return MockCollection(name)

@pytest.fixture(autouse=True)
def mock_db_isolation():
    """
    Autouse fixture that runs before and after each test case.
    Forces testing environment, mocks database connection, pings, and indexing.
    """
    # Preserve original configs
    original_env = settings.APP_ENV
    original_secret = settings.JWT_SECRET_KEY
    original_db = db_manager.db
    original_client = db_manager.client

    # Force configurations for testing
    settings.APP_ENV = "testing"
    if not settings.JWT_SECRET_KEY:
        settings.JWT_SECRET_KEY = "testing_jwt_secret_key_32_chars_or_more_nexora"

    # Set up mock database manager properties
    mock_db = MockDatabase()
    db_manager.db = mock_db
    
    mock_client = MagicMock()
    async def mock_admin_ping(*args, **kwargs):
        return {"ok": 1}
    mock_client.admin.command = mock_admin_ping
    db_manager.client = mock_client

    yield mock_db

    # Clean up and restore original managers
    db_manager.db = original_db
    db_manager.client = original_client
    settings.APP_ENV = original_env
    settings.JWT_SECRET_KEY = original_secret
