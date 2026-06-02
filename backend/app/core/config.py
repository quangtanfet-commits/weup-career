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

from app.core.enums import AssuranceLevel

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

    # Account deletion recovery window (FR-91/92, Luật 91/2025). A deleted
    # account is SOFT-deleted and retained for this many days so the data
    # subject can recover it; a scheduled purge (``python -m app.account.purge``)
    # HARD-deletes accounts whose ``deleted_at`` + this window has elapsed.
    account_recovery_window_days: int = 30

    # Minimum guardian-link assurance required to process an under-16's
    # sensitive data (FF-19, guardian-verification.md §2/§9). Default LOW is the
    # documented MVP interim — VNeID is not yet integrated, so email/OTP consent
    # (LOW) must still unlock processing or no under-16 could use the platform.
    # FLIP TO "medium" ONCE VNEID LANDS so sensitive data needs assured identity.
    sensitive_min_assurance: AssuranceLevel = AssuranceLevel.LOW

    bcrypt_rounds: int = 12

    cors_origins: str = ""

    # Rate limiting (PT-03, ADR-008 §Rate Limiting). Defaults match the ADR
    # bucket table; in-memory fixed-window — see docs/security/http-hardening.md.
    rate_limit_enabled: bool = True
    rate_limit_register_max: int = 5
    rate_limit_register_window_seconds: int = 3600
    rate_limit_login_max: int = 20
    rate_limit_login_window_seconds: int = 60
    rate_limit_refresh_max: int = 60
    rate_limit_refresh_window_seconds: int = 60
    rate_limit_api_max: int = 200
    rate_limit_api_window_seconds: int = 60
    # Resend-verification bucket (N-3). Tighter than register: the email is the
    # only input and each hit sends mail, so cap re-requests per address/window.
    rate_limit_resend_verification_max: int = 3
    rate_limit_resend_verification_window_seconds: int = 3600

    # Email verification (N-3, PT-04 residual). The verification link points at
    # the frontend, which POSTs the token back to /auth/verify-email. TTL bounds
    # how long a single-use token stays valid.
    frontend_base_url: str = "http://localhost:3000"
    verification_token_ttl_hours: int = 24

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
