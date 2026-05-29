"""FastAPI dependency wiring (DI). The HTTP layer assembles services from repos.

Routers depend on these; services never import FastAPI (hexagonal, ADR-009).
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from dataclasses import dataclass

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.assessments.repository import SqlAssessmentRepo
from app.assessments.service import AssessmentService
from app.auth.repository import SqlRefreshTokenRepo, SqlUserRepo
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
from app.core.exceptions import AuthenticationError
from app.core.security import decode_access_token
from app.guardians.repository import SqlGuardianRepo
from app.guardians.service import GuardianService

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


def field_crypto(settings: Settings = Depends(settings_dep)) -> FieldCrypto:
    return FieldCrypto(settings.field_encryption_key)


# -- services -------------------------------------------------------------


def auth_service(
    settings: Settings = Depends(settings_dep),
    users: SqlUserRepo = Depends(user_repo),
    tokens: SqlRefreshTokenRepo = Depends(token_repo),
    audit: SqlAuditRepo = Depends(audit_repo),
) -> AuthService:
    return AuthService(settings=settings, users=users, tokens=tokens, audit=audit)


def guardian_service(
    users: SqlUserRepo = Depends(user_repo),
    guardians: SqlGuardianRepo = Depends(guardian_repo),
    audit: SqlAuditRepo = Depends(audit_repo),
) -> GuardianService:
    return GuardianService(users=users, guardians=guardians, audit=audit)


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
) -> CareerService:
    return CareerService(careers=careers)


# -- auth dependencies ----------------------------------------------------


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    settings: Settings = Depends(settings_dep),
) -> CurrentUser:
    if credentials is None or not credentials.credentials:
        raise AuthenticationError()
    claims = decode_access_token(credentials.credentials, settings=settings)
    return CurrentUser(
        id=str(claims["sub"]),
        email=str(claims.get("email", "")),
        user_type=str(claims.get("user_type", "")),
        age_band=str(claims.get("age_band", "")),
        account_status=str(claims.get("account_status", "")),
        roles=list(claims.get("roles", [])),
    )


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
