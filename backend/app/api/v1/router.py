"""API v1 router aggregator + liveness/readiness probes (ADR-009)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Response, status

from app.account.router import router as account_router
from app.api.deps import get_db
from app.assessments.router import router as assessment_router
from app.auth.router import router as auth_router
from app.careers.router import router as career_router
from app.competency.router import router as competency_router
from app.core.database import Database
from app.guardians.router import router as guardian_router
from app.reco.router import router as reco_router
from app.school.router import router as school_router
from app.wellbeing.router import router as wellbeing_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(guardian_router)
api_router.include_router(assessment_router)
api_router.include_router(competency_router)
api_router.include_router(career_router)
api_router.include_router(reco_router)
api_router.include_router(school_router)
api_router.include_router(wellbeing_router)
api_router.include_router(account_router)


@api_router.get("/health", tags=["ops"])
async def health() -> dict[str, str]:
    """Liveness — always 200 while the process is running."""
    return {"status": "ok"}


@api_router.get("/ready", tags=["ops"])
async def ready(response: Response, db: Database = Depends(get_db)) -> dict[str, Any]:
    """Readiness — 200 if the DB answers, else 503."""
    try:
        await db.ping()
    except Exception:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unavailable", "database": "down"}
    return {"status": "ready", "database": "up"}
