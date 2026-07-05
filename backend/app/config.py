"""Application configuration loaded from environment / .env.

Defaults match the values documented in BACKEND_PLAN.md §5.
"""

from __future__ import annotations

from functools import cached_property

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "sqlite:///./data/calkiller.db"
    jwt_secret: str = "change-me-in-production"
    jwt_alg: str = "HS256"
    jwt_access_ttl_minutes: int = 15
    jwt_refresh_ttl_days: int = 30
    port: int = 8000

    @cached_property
    def database_url_sync(self) -> str:
        """SQLAlchemy sync URL (identical to database_url for the sync stack)."""
        return self.database_url


settings = Settings()
