"""AccountService edge-case unit tests (FR-91/92).

Cover the not-found branches that the happy-path API tests don't reach: a
subject id that resolves via ``can_access`` (self) but has no User row, and a
profile lookup for a non-existent user.
"""

from __future__ import annotations

import pytest
from app.account.repository import SqlAccountRepo
from app.account.service import AccountService
from app.auth.repository import SqlRefreshTokenRepo, SqlUserRepo
from app.core.audit import SqlAuditRepo
from app.core.crypto import FieldCrypto
from app.core.database import Database
from app.core.exceptions import NotFoundError
from app.guardians.repository import SqlGuardianRepo

from tests.conftest import make_settings

pytestmark = pytest.mark.asyncio


def _service(session: object) -> AccountService:
    settings = make_settings()
    return AccountService(
        settings=settings,
        users=SqlUserRepo(session),  # type: ignore[arg-type]
        tokens=SqlRefreshTokenRepo(session),  # type: ignore[arg-type]
        accounts=SqlAccountRepo(session),  # type: ignore[arg-type]
        guardians=SqlGuardianRepo(session),  # type: ignore[arg-type]
        audit=SqlAuditRepo(session),  # type: ignore[arg-type]
        crypto=FieldCrypto(settings.field_encryption_key),
    )


async def test_get_profile_unknown_user_404(db: Database) -> None:
    async with db.session_factory() as s:
        svc = _service(s)
        with pytest.raises(NotFoundError):
            await svc.get_profile("does-not-exist")


async def test_resolve_subject_self_but_missing_row_404(db: Database) -> None:
    """can_access(self) is True, but if the user row is absent the service still
    surfaces NotFound (no phantom subject)."""
    async with db.session_factory() as s:
        svc = _service(s)
        # actor == subject → can_access True, but no such user exists.
        with pytest.raises(NotFoundError):
            await svc.export_data(actor_id="ghost", subject_id="ghost")
