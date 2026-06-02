"""Unit tests for the FileMailer outbox adapter + its DI selection (N-3 e2e infra).

The native Playwright harness drives the same backend process the user runs and
cannot see ``CapturingMailer``'s in-memory list. ``FileMailer`` bridges that gap
by appending each verification link as one NDJSON line to a local outbox file.
These tests pin the append format, multi-send ordering, and that the adapter is
selected ONLY in non-prod when an outbox path is configured (never in prod).
"""

from __future__ import annotations

import json

import pytest
from app.api.deps import mailer as mailer_dep
from app.core.mailer import ConsoleMailer, FileMailer, SmtpMailer

from tests.conftest import make_settings


@pytest.mark.asyncio
async def test_file_mailer_appends_ndjson_line(tmp_path) -> None:
    """One send → one NDJSON line carrying to / verify_url / ts."""
    outbox = tmp_path / "outbox.ndjson"
    mailer = FileMailer(str(outbox))

    await mailer.send_verification_email(
        to="adult@example.com", verify_url="http://fe/verify-email?token=abc"
    )

    lines = outbox.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    row = json.loads(lines[0])
    assert row["to"] == "adult@example.com"
    assert row["verify_url"] == "http://fe/verify-email?token=abc"
    assert isinstance(row["ts"], str) and row["ts"]


@pytest.mark.asyncio
async def test_file_mailer_appends_in_order(tmp_path) -> None:
    """Successive sends append; the newest line is the harness's source of truth."""
    outbox = tmp_path / "outbox.ndjson"
    mailer = FileMailer(str(outbox))

    await mailer.send_verification_email(to="a@b.com", verify_url="http://fe/v?token=old")
    await mailer.send_verification_email(to="a@b.com", verify_url="http://fe/v?token=new")

    lines = outbox.read_text(encoding="utf-8").splitlines()
    assert [json.loads(line)["verify_url"] for line in lines] == [
        "http://fe/v?token=old",
        "http://fe/v?token=new",
    ]


@pytest.mark.asyncio
async def test_file_mailer_creates_parent_dir(tmp_path) -> None:
    """A nested outbox path is created on first write (harness need not pre-mkdir)."""
    outbox = tmp_path / "nested" / "dir" / "outbox.ndjson"
    await FileMailer(str(outbox)).send_verification_email(
        to="a@b.com", verify_url="http://fe/v?token=x"
    )
    assert outbox.is_file()


# -- DI selection ---------------------------------------------------------


def test_di_selects_file_mailer_in_nonprod_with_outbox(tmp_path) -> None:
    s = make_settings(mailer_outbox_path=str(tmp_path / "o.ndjson"))
    assert isinstance(mailer_dep(s), FileMailer)


def test_di_falls_back_to_console_without_outbox() -> None:
    s = make_settings(mailer_outbox_path=None)
    assert isinstance(mailer_dep(s), ConsoleMailer)


def test_di_prod_ignores_outbox_and_uses_smtp(tmp_path) -> None:
    """Production never writes tokens to a local file — SmtpMailer always wins."""
    s = make_settings(environment="production", mailer_outbox_path=str(tmp_path / "o.ndjson"))
    assert isinstance(mailer_dep(s), SmtpMailer)
