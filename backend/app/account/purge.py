"""Hard purge of expired soft-deleted accounts (FR-91/92).

A soft-deleted account is retained for ``ACCOUNT_RECOVERY_WINDOW_DAYS`` so the
data subject can recover it. Once that window has elapsed, the account and ALL
its owned data are HARD-deleted (Luật 91/2025 — right to erasure, with the
documented retention window).

Expiry rule: a user is purged iff ``is_deleted`` AND
``deleted_at <= now - recovery_window``. A user still inside the window is
retained. Each purge writes an audit row (``user.account_purged``).

CLI: ``python -m app.account.purge`` — run on a schedule (cron/operator).
"""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.account.repository import SqlAccountRepo
from app.core.audit import SqlAuditRepo
from app.core.config import Settings, get_settings
from app.core.models import utcnow


async def purge_expired_accounts(
    session: AsyncSession,
    now: datetime,
    *,
    settings: Settings | None = None,
) -> int:
    """Hard-delete every soft-deleted account past its recovery window.

    Returns the number of accounts purged. The caller commits. ``now`` is
    injected so the expiry boundary is testable; ``settings`` defaults to the
    process settings (for the recovery-window length).
    """
    cfg = settings or get_settings()
    cutoff = now - timedelta(days=cfg.account_recovery_window_days)

    accounts = SqlAccountRepo(session)
    audit = SqlAuditRepo(session)

    expired = await accounts.list_expired_deleted(cutoff=cutoff)
    purged = 0
    for user in expired:
        user_id = user.id
        await accounts.hard_delete_user(user)
        # Audit AFTER the row is gone — actor is the system (no actor id).
        await audit.record(
            action="user.account_purged",
            actor_id=None,
            target_type="User",
            target_id=user_id,
        )
        purged += 1
    return purged


async def _run() -> None:  # pragma: no cover - CLI entry point
    """CLI: ``python -m app.account.purge`` — purge expired accounts."""
    from app.core.database import Database

    settings = get_settings()
    db = Database(settings)
    try:
        async with db.session_factory() as session:
            count = await purge_expired_accounts(session, utcnow(), settings=settings)
            await session.commit()
        print(f"[purge] hard-deleted {count} expired account(s)")
    finally:
        await db.dispose()


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    import asyncio

    asyncio.run(_run())
