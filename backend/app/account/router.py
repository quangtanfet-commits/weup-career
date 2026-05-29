"""Account data-rights HTTP routes (spec.md §6, FR-91/92).

Self-service for the authenticated user, plus guardian-acts-for-child variants
(FR-14/92, CP-4) that take an explicit ``child_id`` and authorise via the
relational ``can_access`` path in the service.

Routes:
- ``GET    /me/profile``            view profile (FR-91)
- ``PATCH  /me``                    edit SAFE profile fields (FR-91)
- ``POST   /me/password``           change password (FR-91)
- ``GET    /me/export``             export own data, incl. decrypted results (FR-92, CP-3)
- ``DELETE /me``                    soft-delete own account (FR-91/92)
- ``GET    /me/children/{child_id}/export``  guardian exports a linked child's data
- ``DELETE /me/children/{child_id}``         guardian soft-deletes a linked child's account
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Path, Response, status

from app.account.schemas import (
    DataExport,
    DeletionOut,
    PasswordChangeRequest,
    ProfileOut,
    ProfileUpdateRequest,
)
from app.account.service import AccountService
from app.api.deps import CurrentUser, account_service, get_current_user

router = APIRouter(tags=["account"])


@router.get("/me/profile", response_model=ProfileOut)
async def get_profile(
    current: CurrentUser = Depends(get_current_user),
    service: AccountService = Depends(account_service),
) -> ProfileOut:
    user = await service.get_profile(current.id)
    return ProfileOut.model_validate(user)


@router.patch("/me", response_model=ProfileOut)
async def update_profile(
    payload: ProfileUpdateRequest,
    current: CurrentUser = Depends(get_current_user),
    service: AccountService = Depends(account_service),
) -> ProfileOut:
    user = await service.update_profile(user_id=current.id, payload=payload)
    return ProfileOut.model_validate(user)


@router.post("/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    payload: PasswordChangeRequest,
    current: CurrentUser = Depends(get_current_user),
    service: AccountService = Depends(account_service),
) -> Response:
    await service.change_password(
        user_id=current.id,
        current_password=payload.current_password,
        new_password=payload.new_password,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me/export", response_model=DataExport)
async def export_data(
    current: CurrentUser = Depends(get_current_user),
    service: AccountService = Depends(account_service),
) -> DataExport:
    return await service.export_data(actor_id=current.id, subject_id=current.id)


@router.delete("/me", response_model=DeletionOut)
async def delete_account(
    current: CurrentUser = Depends(get_current_user),
    service: AccountService = Depends(account_service),
) -> DeletionOut:
    result = await service.soft_delete(actor_id=current.id, subject_id=current.id)
    return service.deletion_out(result)


# -- guardian acts for a linked child (FR-14/92, CP-4) --------------------


@router.get("/me/children/{child_id}/export", response_model=DataExport)
async def export_child_data(
    child_id: str = Path(...),
    current: CurrentUser = Depends(get_current_user),
    service: AccountService = Depends(account_service),
) -> DataExport:
    return await service.export_data(actor_id=current.id, subject_id=child_id)


@router.delete("/me/children/{child_id}", response_model=DeletionOut)
async def delete_child_account(
    child_id: str = Path(...),
    current: CurrentUser = Depends(get_current_user),
    service: AccountService = Depends(account_service),
) -> DeletionOut:
    result = await service.soft_delete(actor_id=current.id, subject_id=child_id)
    return service.deletion_out(result)
