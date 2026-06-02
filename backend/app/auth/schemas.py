"""Pydantic v2 schemas for the auth API (FR-01, FR-06)."""

from __future__ import annotations

import re
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.enums import AccountStatus, AgeBand, SchoolLevel, UserType

_UPPER = re.compile(r"[A-Z]")
_LOWER = re.compile(r"[a-z]")
_DIGIT = re.compile(r"\d")


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=256)
    date_of_birth: date
    user_type: UserType = UserType.STUDENT
    school_level: SchoolLevel = SchoolLevel.NONE

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("password")
    @classmethod
    def _password_complexity(cls, value: str) -> str:
        if not (_UPPER.search(value) and _LOWER.search(value) and _DIGIT.search(value)):
            raise ValueError("Mật khẩu phải có chữ hoa, chữ thường và số")
        return value

    @field_validator("date_of_birth")
    @classmethod
    def _dob_in_past(cls, value: date) -> date:
        if value >= date.today():
            raise ValueError("Ngày sinh phải ở quá khứ")
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class VerifyEmailRequest(BaseModel):
    """N-3: the raw single-use token from the verification link."""

    token: str = Field(min_length=1, max_length=512)


class ResendVerificationRequest(BaseModel):
    """N-3: request a fresh verification link. Always answered with a generic
    202 regardless of whether the email exists / is already verified (§5)."""

    email: EmailStr

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class AcceptedResponse(BaseModel):
    """Generic 202 body for register / resend-verification.

    Deliberately carries NO account data and NO session: a single, constant
    message for every input so neither endpoint becomes an enumeration oracle
    (spec §2.1/§5). The frontend shows a "check your email" screen on 202.
    """

    message: str = (
        "Nếu thông tin hợp lệ, chúng tôi đã gửi email xác minh. Vui lòng kiểm tra hộp thư."
    )


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    age_band: AgeBand
    user_type: UserType
    school_level: SchoolLevel
    account_status: AccountStatus
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut
