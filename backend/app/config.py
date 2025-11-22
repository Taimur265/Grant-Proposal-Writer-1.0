"""Application configuration settings."""

from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Grant Proposal Writer"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "your-secret-key-change-in-production"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/grant_writer"
    DATABASE_SYNC_URL: str = "postgresql://postgres:postgres@localhost:5432/grant_writer"

    # JWT Settings
    JWT_SECRET_KEY: str = "jwt-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # AI Provider Settings
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    DEFAULT_AI_PROVIDER: str = "openai"  # or "anthropic"
    DEFAULT_MODEL: str = "gpt-4-turbo-preview"

    # File Upload Settings
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: list = [
        ".pdf", ".docx", ".doc", ".txt", ".xlsx", ".xls",
        ".pptx", ".ppt", ".rtf", ".odt", ".csv"
    ]
    UPLOAD_DIR: str = "./uploads"

    # Storage Settings (MinIO/S3)
    STORAGE_TYPE: str = "local"  # "local", "s3", or "minio"
    S3_ENDPOINT: Optional[str] = None
    S3_ACCESS_KEY: Optional[str] = None
    S3_SECRET_KEY: Optional[str] = None
    S3_BUCKET_NAME: str = "grant-proposals"
    S3_REGION: str = "us-east-1"

    # CORS Settings
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:8000"]

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
