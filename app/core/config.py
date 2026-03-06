from functools import lru_cache
from typing import List, Literal
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from pydantic import SecretStr


class Settings(BaseSettings):
    """Enterprise application configuration."""

    # ------------------------------------------------------------------
    # Environment
    # ------------------------------------------------------------------
    ENVIRONMENT: Literal["dev", "staging", "prod"] = "dev"
    DEBUG: bool = False

    # ------------------------------------------------------------------
    # Service
    # ------------------------------------------------------------------
    SERVICE_NAME: str = "Artifact Report Generator"
    SERVICE_VERSION: str = "1.0.0"
    CREATED_BY: str = "Mokshith Balidi"

    # ------------------------------------------------------------------
    # Server
    # ------------------------------------------------------------------
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4

    # ------------------------------------------------------------------
    # API
    # ------------------------------------------------------------------
    API_PREFIX: str = "/api/v1"

    # ------------------------------------------------------------------
    # AI
    # ------------------------------------------------------------------
    GEMINI_API_KEY: SecretStr
    GEMINI_MODEL: str = "gemini-2.0-flash"

    # ------------------------------------------------------------------
    # Rate Limiting
    # ------------------------------------------------------------------
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 30

    # ------------------------------------------------------------------
    # File Upload
    # ------------------------------------------------------------------
    MAX_ZIP_SIZE_MB: int = 500
    UPLOAD_TIMEOUT_SECONDS: int = 300

    # ------------------------------------------------------------------
    # Error Tracking
    # ------------------------------------------------------------------
    SENTRY_DSN: SecretStr | None = None
    SENTRY_TRACES_SAMPLE_RATE: float = 1.0
    SENTRY_PROFILES_SAMPLE_RATE: float = 1.0

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # ------------------------------------------------------------------
    # CORS / Security
    # ------------------------------------------------------------------
    CORS_ORIGINS: List[str] = ["*"]
    TRUSTED_HOSTS: List[str] = []
    
    # ------------------------------------------------------------------
    # API KEY / Security
    # ------------------------------------------------------------------
    
    API_KEY_ENABLED: bool = True
    API_KEY: SecretStr | None = None
    API_KEY_HEADER: str = "X-API-Key"

    # ------------------------------------------------------------------
    # Computed
    # ------------------------------------------------------------------
    @property
    def MAX_ZIP_SIZE_BYTES(self) -> int:
        return self.MAX_ZIP_SIZE_MB * 1024 * 1024

    @property
    def SENTRY_ENABLED(self) -> bool:
        return self.SENTRY_DSN is not None

    # ------------------------------------------------------------------
    # Validators
    # ------------------------------------------------------------------
    @field_validator("PORT")
    def validate_port(cls, v):
        if not (1 <= v <= 65535):
            raise ValueError("PORT must be between 1 and 65535")
        return v

    @field_validator("WORKERS")
    def validate_workers(cls, v):
        if v < 1:
            raise ValueError("WORKERS must be >= 1")
        return v

    @field_validator("RATE_LIMIT_PER_MINUTE")
    def validate_rate_limit(cls, v):
        if v < 1:
            raise ValueError("RATE_LIMIT_PER_MINUTE must be >= 1")
        return v

    @field_validator("MAX_ZIP_SIZE_MB")
    def validate_zip_size(cls, v):
        if v < 1:
            raise ValueError("MAX_ZIP_SIZE_MB must be >= 1")
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
