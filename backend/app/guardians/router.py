"""Guardian HTTP routes (spec.md §6): invite/consent/revoke."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status

from app.api.deps import CurrentUser, get_current_user, guardian_service
from app.guardians.schemas import (
    ConsentOut,
    ConsentRequest,
    GuardianLinkOut,
    InviteRequest,
    RevokeRequest,
)
from app.guardians.service import GuardianService

router = APIRouter(prefix="/guardians", tags=["guardians"])


@router.post("/invite", response_model=GuardianLinkOut, status_code=status.HTTP_201_CREATED)
async def invite(
    payload: InviteRequest,
    current: CurrentUser = Depends(get_current_user),
    service: GuardianService = Depends(guardian_service),
) -> GuardianLinkOut:
    link = await service.invite(child_user_id=current.id, payload=payload)
    return GuardianLinkOut.model_validate(link)


@router.post("/consent", response_model=ConsentOut, status_code=status.HTTP_201_CREATED)
async def grant_consent(
    payload: ConsentRequest,
    current: CurrentUser = Depends(get_current_user),
    service: GuardianService = Depends(guardian_service),
) -> ConsentOut:
    consent = await service.grant_consent(
        guardian_user_id=current.id, guardian_link_id=payload.guardian_link_id
    )
    return ConsentOut.model_validate(consent)


@router.post("/consent/revoke", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_consent(
    payload: RevokeRequest,
    current: CurrentUser = Depends(get_current_user),
    service: GuardianService = Depends(guardian_service),
) -> Response:
    await service.revoke_consent(guardian_user_id=current.id, child_user_id=payload.child_user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
