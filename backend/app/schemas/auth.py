from uuid import UUID

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AuthenticatedApplicationUserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    auth_user_id: UUID
    email: str
    full_name: str
    role: str
    is_active: bool


class SignupProvisionRequest(BaseModel):
    role: Literal["BIDDER", "OFFICER"]
    full_name: str = Field(min_length=1, max_length=255)
    legal_name: str | None = Field(default=None, max_length=255)
    registration_number: str | None = Field(default=None, max_length=255)
    gst_number: str | None = Field(default=None, max_length=255)
    pan_number: str | None = Field(default=None, max_length=255)

    @field_validator("full_name")
    @classmethod
    def normalize_full_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Full name is required.")
        return normalized

    @field_validator("legal_name", "registration_number", "gst_number", "pan_number")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class SignupProvisionResponse(BaseModel):
    user_id: UUID
    auth_user_id: UUID
    role: Literal["BIDDER", "OFFICER"]
    profile_id: UUID
