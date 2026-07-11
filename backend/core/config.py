from pydantic_settings import BaseSettings, SettingsConfigDict

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

    # Configuration for Pydantic settings loading
    model_config = SettingsConfigDict(
        env_file=".env",
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
