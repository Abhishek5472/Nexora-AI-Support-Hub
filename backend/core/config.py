import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Get paths relative to this config file
CURRENT_DIR = Path(__file__).parent.resolve()
BACKEND_ROOT = CURRENT_DIR.parent.resolve()
WORKSPACE_ROOT = BACKEND_ROOT.parent.resolve()

class Settings(BaseSettings):
    """
    Application Settings configuration utilizing Pydantic Settings.
    Environment variables are mapped automatically, case-sensitively by default.
    """
    APP_NAME: str = "Nexora AI Support Hub API"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    BACKEND_HOST: str = "127.0.0.1"
    BACKEND_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:3000"
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    
    # MongoDB settings (can be empty/unconfigured)
    MONGODB_URI: str = ""
    MONGODB_DATABASE: str = "nexora_support_db"

    # JWT & Cookie Security configurations
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    REFRESH_COOKIE_NAME: str = "refresh_token"
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: str = "lax"

    # RAG / Knowledge Base configurations
    KNOWLEDGE_BASE_PATH: str = str(WORKSPACE_ROOT / "knowledge_base")
    VECTOR_STORE_PATH: str = str(WORKSPACE_ROOT / "vectorstore")
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    EMBEDDING_BATCH_SIZE: int = 32
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    RETRIEVAL_TOP_K: int = 5
    RETRIEVAL_SCORE_THRESHOLD: float = 0.0
    MAX_KNOWLEDGE_FILE_SIZE_MB: int = 10

    # Configuration for Pydantic settings loading. Workspace root overrides backend-specific defaults.
    model_config = SettingsConfigDict(
        env_file=(
            os.path.join(BACKEND_ROOT, ".env"),
            os.path.join(WORKSPACE_ROOT, ".env"),
        ),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """
        Parses the comma-separated CORS_ORIGINS string into a list.
        """
        if not self.CORS_ORIGINS:
            return []
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

# Global settings instance
settings = Settings()
