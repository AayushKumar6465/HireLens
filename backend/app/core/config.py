"""
Application configuration loaded from environment variables.

All settings are read from the environment (or backend/.env via pydantic-settings).
Secrets must never be hardcoded here.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated application settings from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Runtime
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"
    frontend_origin: str = "http://localhost:5173"

    # Database
    database_url: str = ""

    # JWT
    jwt_secret: str = "change-me-use-a-long-random-string"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # File upload
    upload_dir: str = "./storage/resumes"
    max_upload_mb: int = 5
    max_files_per_batch: int = 20

    # Scoring
    embeddings_enabled: bool = False
    weight_skills: float = 0.40
    weight_semantic: float = 0.30
    weight_experience: float = 0.20
    weight_education: float = 0.10


settings = Settings()
