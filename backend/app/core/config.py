"""
Application configuration loaded from environment variables.

All settings are read from the environment (or backend/.env via pydantic-settings).
Secrets must never be hardcoded here.
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_backend_env = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    """Validated application settings from environment variables."""

    model_config = SettingsConfigDict(
        env_file=(str(_backend_env), ".env"),
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


def validate_jwt_secret_for_startup() -> None:
    """Enforce strong JWT secret key; fail startup if placeholder or < 32 characters."""
    secret = settings.jwt_secret.strip() if settings.jwt_secret else ""
    if not secret or secret == "change-me-use-a-long-random-string" or len(secret) < 32:
        raise RuntimeError(
            "Application startup failed: JWT_SECRET cannot be the default placeholder and must be at least 32 characters long."
        )


settings = Settings()
