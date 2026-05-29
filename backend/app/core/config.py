"""Application configuration (12-factor, env-driven).

Reads settings from environment / `.env`. Secrets (`SECRET_KEY`,
`FIELD_ENCRYPTION_KEY`) may also be read from a file path (Docker secrets,
ADR-006 / [CRED_3D2D8FFB]) by setting `*_FILE` env vars.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["development", "production", "test"]


def _read_secret(value: str, file_env: str) -> str:
    """Resolve a secret: explicit `*_FILE` path wins over the inline value."""
    file_path = os.environ.get(file_env)
    if file_path and os.path.isfile(file_path):
        with open(file_path, encoding="utf-8") as handle:
            return handle.read().strip()
    return value


class Settings(BaseSettings):
    """Typed application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    environment: Environment = "development"
    log_level: str = "info"

    # Secrets — generate via `openssl rand -hex 32`.
    secret_key: str = Field(min_length=32)
    field_encryption_key: str = Field(min_length=32)

    database_url: str = "sqlite+aiosqlite:///./data/app.db"

    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "weup-api"

    # Guardian-consent age boundary (legal-basis §6 / NĐ 147/2024).
    consent_age_threshold: int = 16

    bcrypt_rounds: int = 12

    cors_origins: str = ""

    @field_validator("secret_key", "field_encryption_key", mode="before")
    @classmethod
    def _resolve_from_file(cls, value: str, info: object) -> str:
        # info.field_name is available at runtime; map to the *_FILE env var.
        field_name = getattr(info, "field_name", "")
        return _read_secret(str(value), f"{field_name.upper()}_FILE")

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor (one instance per process)."""
    return Settings()
