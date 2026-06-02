"""FastAPI dependency wiring (DI). The HTTP layer assembles services from repos.

Routers depend on these; services never import FastAPI (hexagonal, ADR-009).
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.account.repository import SqlAccountRepo
from app.account.service import AccountService
from app.assessments.repository import SqlAssessmentRepo
from app.assessments.service import AssessmentService
from app.auth.repository import (
    SqlEmailVerificationTokenRepo,
    SqlRefreshTokenRepo,
    SqlRevokedTokenRepo,
    SqlUserRepo,
)
from app.auth.service import AuthService
from app.careers.repository import SqlCareerRepo
from app.careers.service import CareerService
from app.competency.repository import SqlCompetencyRepo
from app.competency.service import CompetencyService
from app.core.audit import SqlAuditRepo
from app.core.config import Settings, get_settings
from app.core.consent import require_consent
from app.core.crypto import FieldCrypto
from app.core.database import Database
from app.core.exceptions import AuthenticationError, PermissionDeniedError
from app.core.mailer import ConsoleMailer, FileMailer, IMailer, SmtpMailer
from app.core.security import decode_access_token
from app.guardians.repository import SqlGuardianRepo
from app.guardians.service import GuardianService
from app.reco.repository import SqlRecoRepo
from app.reco.service import RecoService
from app.school.repository import SqlSchoolRepo
from app.school.service import SchoolService
from app.wellbeing.repository import SqlWellbeingRepo
from app.wellbeing.service import WellbeingService

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentUser:
    """Identity extracted from a verified access token."""

    id: str
    email: str
    user_type: str
    age_band: str
    account_status: str
    roles: list[str]
    # Access-token identity for revocation (H-01). Defaulted so non-HTTP
    # constructions (tests, internal callers) need not supply them.
    jti: str = ""
    token_exp: int = 0


def get_db(request: Request) -> Database:
    db: Database = request.app.state.db
    return db


async def get_session(
    db: Database = Depends(get_db),
) -> AsyncGenerator[AsyncSession, None]:
    async for session in db.session():
        yield session


def settings_dep(request: Request) -> Settings:
    """Resolve the app's configured settings (set on app.state at startup)."""
    configured: Settings | None = getattr(request.app.state, "settings", None)
    return configured if configured is not None else get_settings()


# -- repositories ---------------------------------------------------------


def user_repo(session: AsyncSession = Depends(get_session)) -> SqlUserRepo:
    return SqlUserRepo(session)


def token_repo(session: AsyncSession = Depends(get_session)) -> SqlRefreshTokenRepo:
    return SqlRefreshTokenRepo(session)


def revoked_token_repo(
    session: AsyncSession = Depends(get_session),
) -> SqlRevokedTokenRepo:
    return SqlRevokedTokenRepo(session)


def email_verification_repo(
    session: AsyncSession = Depends(get_session),
) -> SqlEmailVerificationTokenRepo:
    return SqlEmailVerificationTokenRepo(session)


def guardian_repo(session: AsyncSession = Depends(get_session)) -> SqlGuardianRepo:
    return SqlGuardianRepo(session)


def audit_repo(session: AsyncSession = Depends(get_session)) -> SqlAuditRepo:
    return SqlAuditRepo(session)


def assessment_repo(session: AsyncSession = Depends(get_session)) -> SqlAssessmentRepo:
    return SqlAssessmentRepo(session)


def competency_repo(session: AsyncSession = Depends(get_session)) -> SqlCompetencyRepo:
    return SqlCompetencyRepo(session)


def career_repo(session: AsyncSession = Depends(get_session)) -> SqlCareerRepo:
    return SqlCareerRepo(session)


def reco_repo(session: AsyncSession = Depends(get_session)) -> SqlRecoRepo:
    return SqlRecoRepo(session)


def school_repo(session: AsyncSession = Depends(get_session)) -> SqlSchoolRepo:
    return SqlSchoolRepo(session)


def wellbeing_repo(session: AsyncSession = Depends(get_session)) -> SqlWellbeingRepo:
    return SqlWellbeingRepo(session)


def account_repo(session: AsyncSession = Depends(get_session)) -> SqlAccountRepo:
    return SqlAccountRepo(session)


def field_crypto(settings: Settings = Depends(settings_dep)) -> FieldCrypto:
    return FieldCrypto(settings.field_encryption_key)


def mailer(settings: Settings = Depends(settings_dep)) -> IMailer:
    # No real SMTP ships in the MVP (N-3 §8): dev/test log or capture the link,
    # production fail-fasts rather than silently dropping verification mail or
    # leaking the token to logs. Tests override this with a CapturingMailer.
    if settings.is_production:
        return SmtpMailer()
    # Non-prod with a configured outbox → FileMailer, so the out-of-process E2E
    # harness can read the raw token (NDJSON outbox). Otherwise log to console.
    if settings.mailer_outbox_path:
        return FileMailer(settings.mailer_outbox_path)
    return ConsoleMailer()


# -- services -------------------------------------------------------------


def auth_service(
    settings: Settings = Depends(settings_dep),
    users: SqlUserRepo = Depends(user_repo),
    tokens: SqlRefreshTokenRepo = Depends(token_repo),
    revoked: SqlRevokedTokenRepo = Depends(revoked_token_repo),
    email_tokens: SqlEmailVerificationTokenRepo = Depends(email_verification_repo),
    mailer_: IMailer = Depends(mailer),
    audit: SqlAuditRepo = Depends(audit_repo),
) -> AuthService:
    return AuthService(
        settings=settings,
        users=users,
        tokens=tokens,
        revoked=revoked,
        email_tokens=email_tokens,
        mailer=mailer_,
        audit=audit,
    )


def guardian_service(
    users: SqlUserRepo = Depends(user_repo),
    guardians: SqlGuardianRepo = Depends(guardian_repo),
    audit: SqlAuditRepo = Depends(audit_repo),
) -> GuardianService:
    return GuardianService(users=users, guardians=guardians, audit=audit)


def account_service(
    settings: Settings = Depends(settings_dep),
    users: SqlUserRepo = Depends(user_repo),
    tokens: SqlRefreshTokenRepo = Depends(token_repo),
    accounts: SqlAccountRepo = Depends(account_repo),
    guardians: SqlGuardianRepo = Depends(guardian_repo),
    audit: SqlAuditRepo = Depends(audit_repo),
    crypto: FieldCrypto = Depends(field_crypto),
) -> AccountService:
    return AccountService(
        settings=settings,
        users=users,
        tokens=tokens,
        accounts=accounts,
        guardians=guardians,
        audit=audit,
        crypto=crypto,
    )


def assessment_service(
    settings: Settings = Depends(settings_dep),
    assessments: SqlAssessmentRepo = Depends(assessment_repo),
    guardians: SqlGuardianRepo = Depends(guardian_repo),
    audit: SqlAuditRepo = Depends(audit_repo),
    crypto: FieldCrypto = Depends(field_crypto),
) -> AssessmentService:
    return AssessmentService(
        settings=settings,
        assessments=assessments,
        guardians=guardians,
        audit=audit,
        crypto=crypto,
    )


def competency_service(
    competencies: SqlCompetencyRepo = Depends(competency_repo),
    users: SqlUserRepo = Depends(user_repo),
    audit: SqlAuditRepo = Depends(audit_repo),
) -> CompetencyService:
    return CompetencyService(competencies=competencies, users=users, audit=audit)


def career_service(
    careers: SqlCareerRepo = Depends(career_repo),
    audit: SqlAuditRepo = Depends(audit_repo),
) -> CareerService:
    return CareerService(careers=careers, audit=audit)


def reco_service(
    recos: SqlRecoRepo = Depends(reco_repo),
    audit: SqlAuditRepo = Depends(audit_repo),
    crypto: FieldCrypto = Depends(field_crypto),
    guardians: SqlGuardianRepo = Depends(guardian_repo),
    schools: SqlSchoolRepo = Depends(school_repo),
) -> RecoService:
    return RecoService(
        reco=recos,
        audit=audit,
        crypto=crypto,
        guardians=guardians,
        counselor_access=schools.has_counselor_access,
    )


def school_service(
    schools: SqlSchoolRepo = Depends(school_repo),
    guardians: SqlGuardianRepo = Depends(guardian_repo),
    competency: CompetencyService = Depends(competency_service),
    recos: SqlRecoRepo = Depends(reco_repo),
    audit: SqlAuditRepo = Depends(audit_repo),
    crypto: FieldCrypto = Depends(field_crypto),
    users: SqlUserRepo = Depends(user_repo),
) -> SchoolService:
    return SchoolService(
        school=schools,
        guardians=guardians,
        competency=competency,
        reco=recos,
        audit=audit,
        crypto=crypto,
        users=users,
    )


def wellbeing_service(
    wellbeing: SqlWellbeingRepo = Depends(wellbeing_repo),
    audit: SqlAuditRepo = Depends(audit_repo),
    schools: SqlSchoolRepo = Depends(school_repo),
) -> WellbeingService:
    return WellbeingService(
        wellbeing=wellbeing,
        audit=audit,
        find_counselor=schools.find_counselor_for_student,
    )


# -- auth dependencies ----------------------------------------------------


def _user_from_claims(claims: dict[str, Any]) -> CurrentUser:
    return CurrentUser(
        id=str(claims["sub"]),
        email=str(claims.get("email", "")),
        user_type=str(claims.get("user_type", "")),
        age_band=str(claims.get("age_band", "")),
        account_status=str(claims.get("account_status", "")),
        roles=list(claims.get("roles", [])),
        jti=str(claims.get("jti", "")),
        token_exp=int(claims.get("exp", 0)),
    )


async def _reject_if_revoked(claims: dict[str, Any], revoked: SqlRevokedTokenRepo) -> None:
    """Reject an access token whose ``jti`` has been denylisted on logout (H-01).

    Stateless JWTs (ADR-008) stay cryptographically valid until ``exp``; this is
    the only per-request hook that can tear one down early. A token with no
    ``jti`` (legacy/None) is never denylistable and falls through unchanged.
    """
    jti = claims.get("jti")
    if jti and await revoked.is_revoked(str(jti), now=datetime.now(UTC)):
        raise AuthenticationError()


async def _reject_if_stale_session(claims: dict[str, Any], users: SqlUserRepo) -> None:
    """Reject an access token whose session epoch is below the user's current one (H-02).

    Re-login and password change bump ``User.session_version``; a token minted
    before the bump carries an ``sv`` claim below the live value and is rejected,
    invalidating *all* prior access tokens at once. A token with no ``sv`` claim
    (legacy, pre-H-02) falls through unchanged so a deploy does not mass-401 live
    sessions; a missing user (``None``) is left to the existing identity checks.
    """
    sv = claims.get("sv")
    if sv is None:
        return
    current = await users.current_session_version(str(claims["sub"]))
    if current is not None and int(sv) < current:
        raise AuthenticationError()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    settings: Settings = Depends(settings_dep),
    revoked: SqlRevokedTokenRepo = Depends(revoked_token_repo),
    users: SqlUserRepo = Depends(user_repo),
) -> CurrentUser:
    if credentials is None or not credentials.credentials:
        raise AuthenticationError()
    claims = decode_access_token(credentials.credentials, settings=settings)
    await _reject_if_revoked(claims, revoked)
    await _reject_if_stale_session(claims, users)
    return _user_from_claims(claims)


async def optional_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    settings: Settings = Depends(settings_dep),
    revoked: SqlRevokedTokenRepo = Depends(revoked_token_repo),
    users: SqlUserRepo = Depends(user_repo),
) -> CurrentUser | None:
    """Resolve the Bearer identity if present; ``None`` for an anonymous caller.

    Used by the Điều-5(a) public-read routes (career library + 5c/5d learning
    content) so the frontend can serve them as public SEO pages WITHOUT a login
    (BE-1; ADR-001 §Consequences — Điều-5a is công khai). Policy:

    - **No / empty Authorization header → ``None``** (anonymous allowed). The
      route then enforces the published-only invariant for unauthenticated
      callers.
    - **Present but invalid/expired token → 401** (``TokenError``). A malformed
      token is an explicit attempt to authenticate; silently accepting it as
      anonymous would mask client bugs and hide token-tampering, so it is
      rejected rather than downgraded.
    """
    if credentials is None or not credentials.credentials:
        return None
    claims = decode_access_token(credentials.credentials, settings=settings)
    await _reject_if_revoked(claims, revoked)
    await _reject_if_stale_session(claims, users)
    return _user_from_claims(claims)


async def require_content_editor(
    current: CurrentUser = Depends(get_current_user),
    users: SqlUserRepo = Depends(user_repo),
) -> CurrentUser:
    """Authorise a global content_editor (FR-90), re-derived from the DB.

    The JWT ``roles`` claim is only a hint; authority is re-validated against
    ``User.is_content_editor`` per request (a claim can be up to 15' stale, and
    a revoked editor must lose access immediately). A non-editor → 403.
    """
    user = await users.get_by_id(current.id)
    if user is None or not user.is_content_editor:
        raise PermissionDeniedError("Chỉ biên tập viên nội dung mới được thực hiện")
    return current


async def require_career_data_consent(
    current: CurrentUser = Depends(get_current_user),
    guardians: SqlGuardianRepo = Depends(guardian_repo),
) -> CurrentUser:
    """Consent Guard dependency for career-data routes (CP-1/CP-2).

    Re-validates against the DB regardless of the (possibly stale) JWT claim.
    Wire this into assessment/recommendation/progress routes in later slices.
    """
    await require_consent(user_id=current.id, age_band=current.age_band, guardian_repo=guardians)
    return current
