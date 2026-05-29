"""Age-band derivation + config secret-file resolution unit tests."""

from __future__ import annotations

from datetime import date

from app.auth.age import calculate_age, derive_age_band
from app.core.config import Settings, get_settings
from app.core.enums import AgeBand


def test_calculate_age_before_birthday() -> None:
    today = date(2026, 5, 29)
    # birthday is tomorrow → still previous age
    assert calculate_age(date(2010, 5, 30), today=today) == 15


def test_calculate_age_on_birthday() -> None:
    today = date(2026, 5, 29)
    assert calculate_age(date(2010, 5, 29), today=today) == 16


def test_derive_under_16() -> None:
    today = date(2026, 5, 29)
    assert derive_age_band(date(2012, 1, 1), today=today) == AgeBand.UNDER_16


def test_derive_16_17() -> None:
    today = date(2026, 5, 29)
    assert derive_age_band(date(2009, 1, 1), today=today) == AgeBand.BAND_16_17


def test_derive_adult() -> None:
    today = date(2026, 5, 29)
    assert derive_age_band(date(2000, 1, 1), today=today) == AgeBand.ADULT


def test_threshold_is_configurable() -> None:
    today = date(2026, 5, 29)
    # With threshold 18 a 16-year-old is treated as under-16 band (consent gate).
    assert derive_age_band(date(2009, 1, 1), today=today, threshold=18) == AgeBand.UNDER_16


def test_settings_reads_secret_from_file(tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    secret_file = tmp_path / "secret"
    secret_file.write_text("filesecret-0123456789012345678901234567")
    monkeypatch.setenv("SECRET_KEY_FILE", str(secret_file))
    monkeypatch.setenv("SECRET_KEY", "inline-ignored-0000000000000000000000")
    monkeypatch.setenv("FIELD_ENCRYPTION_KEY", "field-0123456789012345678901234567")
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    s = Settings(_env_file=None)  # type: ignore[call-arg]
    assert s.secret_key == "filesecret-0123456789012345678901234567"


def test_settings_helpers() -> None:
    s = Settings(  # type: ignore[call-arg]
        secret_key="x" * 32,
        field_encryption_key="y" * 32,
        environment="production",
        cors_origins="https://a.com, https://b.com",
        _env_file=None,
    )
    assert s.is_production is True
    assert s.cors_origin_list == ["https://a.com", "https://b.com"]


def test_get_settings_cached(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("SECRET_KEY", "k" * 32)
    monkeypatch.setenv("FIELD_ENCRYPTION_KEY", "j" * 32)
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    get_settings.cache_clear()
    a = get_settings()
    b = get_settings()
    assert a is b
    get_settings.cache_clear()
