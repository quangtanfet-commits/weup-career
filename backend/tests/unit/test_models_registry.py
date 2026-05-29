"""The models registry must expose every mapped table for Alembic/[CRED_DB22DB7C]."""

from __future__ import annotations

from app.models_registry import Base


def test_all_slice1_tables_registered() -> None:
    tables = set(Base.metadata.tables.keys())
    assert {
        "user",
        "refresh_token",
        "guardian_link",
        "guardian_consent",
        "audit_log",
    } <= tables
