"""Domain exceptions mapped to the API error schema.

Error response shape (architecture/overview.md §"Error Response Schema"):

    {"error": {"code": ..., "message": ..., "details": {}, "request_id": ...}}
"""

from __future__ import annotations

from typing import Any


class AppError(Exception):
    """Base application error carrying an HTTP status and a stable code."""

    status_code: int = 500
    code: str = "INTERNAL_ERROR"
    message: str = "Lỗi nội bộ"

    def __init__(
        self,
        message: str | None = None,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message or self.message
        self.details: dict[str, Any] = details or {}
        super().__init__(self.message)


class ValidationError(AppError):
    status_code = 422
    code = "VALIDATION_ERROR"
    message = "Dữ liệu không hợp lệ"


class AuthenticationError(AppError):
    status_code = 401
    code = "AUTHENTICATION_REQUIRED"
    message = "Yêu cầu xác thực"


class InvalidCredentialsError(AppError):
    status_code = 401
    code = "INVALID_CREDENTIALS"
    message = "Email hoặc mật khẩu không đúng"


class TokenError(AuthenticationError):
    code = "INVALID_TOKEN"
    message = "Token không hợp lệ hoặc đã hết hạn"


class PermissionDeniedError(AppError):
    status_code = 403
    code = "PERMISSION_DENIED"
    message = "Không đủ quyền"


class GuardianConsentRequiredError(AppError):
    """CP-1 / [CRED_85F77B7A]: under-16 may not process career data without active consent."""

    status_code = 403
    code = "GUARDIAN_CONSENT_REQUIRED"
    message = (
        "Tài khoản dưới 16 tuổi cần đồng ý của người giám hộ "
        "trước khi xử lý dữ liệu hướng nghiệp"
    )


class NotFoundError(AppError):
    status_code = 404
    code = "NOT_FOUND"
    message = "Không tìm thấy"


class ConflictError(AppError):
    status_code = 409
    code = "CONFLICT"
    message = "Xung đột dữ liệu"


class SelfConsentError(AppError):
    """ADR-010: a child cannot act as their own guardian."""

    status_code = 403
    code = "SELF_CONSENT_FORBIDDEN"
    message = "Không thể tự đóng vai người giám hộ cho chính mình"


class RationaleRequiredError(AppError):
    """CP-6 / [CRED_2FB3E29D]: a recommendation can never be created without a rationale.

    Defence-in-depth alongside the ``Recommendation.rationale`` NOT NULL column:
    the service raises this before persisting if the rationale is empty.
    """

    status_code = 422
    code = "RATIONALE_REQUIRED"
    message = "Gợi ý bắt buộc phải có lý do (rationale) — không thể tạo gợi ý rỗng lý do"


class AssuranceTooLowError(AppError):
    """FF-19: under-16 sensitive data needs a minimum guardian-link assurance."""

    status_code = 403
    code = "ASSURANCE_LEVEL_TOO_LOW"
    message = (
        "Mức xác thực người giám hộ chưa đủ để xử lý dữ liệu nhạy cảm "
        "của người dùng dưới 16 tuổi"
    )
