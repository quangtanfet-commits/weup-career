"""Auth HTTP routes (spec.md §6): register/login/refresh/logout/me."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response, status

from app.api.deps import (
    CurrentUser,
    auth_service,
    get_current_user,
    settings_dep,
)
from app.auth.schemas import (
    AcceptedResponse,
    LoginRequest,
    RegisterRequest,
    ResendVerificationRequest,
    TokenResponse,
    UserOut,
    VerifyEmailRequest,
)
from app.auth.service import AuthService, IssuedTokens
from app.core.config import Settings
from app.core.exceptions import NotFoundError, TokenError

router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_COOKIE = "refresh_token"


def _set_refresh_cookie(response: Response, raw_token: str, settings: Settings) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=raw_token,
        max_age=settings.refresh_token_expire_days * 24 * 3600,
        httponly=True,
        secure=settings.is_production,
        samesite="strict",
        path="/api/v1/auth",
    )


def _token_response(response: Response, issued: IssuedTokens, settings: Settings) -> TokenResponse:
    _set_refresh_cookie(response, issued.refresh_token, settings)
    return TokenResponse(
        access_token=issued.access_token,
        expires_in=issued.expires_in,
        user=UserOut.model_validate(issued.user),
    )


@router.post(
    "/register",
    response_model=AcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def register(
    payload: RegisterRequest,
    service: AuthService = Depends(auth_service),
) -> AcceptedResponse:
    # N-3: always 202 with a generic body — no UserOut, no session. The reply is
    # identical for a brand-new, duplicate, or otherwise-handled email so the
    # endpoint never becomes an enumeration oracle (spec §2.1/§5). The service
    # decides internally whether a real account + verification mail is created.
    await service.register(payload)
    return AcceptedResponse()


@router.post("/verify-email", status_code=status.HTTP_204_NO_CONTENT)
async def verify_email(
    payload: VerifyEmailRequest,
    service: AuthService = Depends(auth_service),
) -> Response:
    # N-3: every failure (unknown / [CRED_47E73CB6] / [CRED_5FFEE6AB] token) is one generic
    # TokenError (401) — never reveals whether the token existed (spec §5).
    await service.verify_email(payload.token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/resend-verification",
    response_model=AcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def resend_verification(
    payload: ResendVerificationRequest,
    service: AuthService = Depends(auth_service),
) -> AcceptedResponse:
    # N-3: always 202 with a generic body regardless of whether the address
    # exists or is already verified — the real send happens only internally for a
    # live, still-unverified account (spec §5). Rate-limited in middleware.
    await service.resend_verification(payload.email)
    return AcceptedResponse()


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    service: AuthService = Depends(auth_service),
    settings: Settings = Depends(settings_dep),
) -> TokenResponse:
    issued = await service.login(
        payload,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )
    return _token_response(response, issued, settings)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: Request,
    response: Response,
    service: AuthService = Depends(auth_service),
    settings: Settings = Depends(settings_dep),
) -> TokenResponse:
    raw = request.cookies.get(REFRESH_COOKIE)
    if not raw:
        raise TokenError()
    issued = await service.refresh(
        raw,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )
    return _token_response(response, issued, settings)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    _current: CurrentUser = Depends(get_current_user),
    service: AuthService = Depends(auth_service),
) -> Response:
    await service.logout(
        request.cookies.get(REFRESH_COOKIE),
        access_jti=_current.jti,
        access_exp=_current.token_exp,
        user_id=_current.id,
    )
    response.delete_cookie(REFRESH_COOKIE, path="/api/v1/auth")
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/me", response_model=UserOut)
async def me(
    current: CurrentUser = Depends(get_current_user),
    service: AuthService = Depends(auth_service),
) -> UserOut:
    user = await service.get_user(current.id)
    if user is None:
        raise NotFoundError("Không tìm thấy người dùng")
    return UserOut.model_validate(user)
