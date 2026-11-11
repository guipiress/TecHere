from datetime import datetime
from typing import Annotated

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    StringConstraints,
)

from backend.app.schemas.common import PersonName

EMAIL_MAX_LENGTH = 255  # users.email is VARCHAR(255)


def _normalize_email(value: str) -> str:
    # The UNIQUE constraint on users.email is case-sensitive, so without
    # normalisation "Ana@x.com" and "ana@x.com" would become two accounts.
    # That is a duplicate-account / account-takeover risk once login exists.
    value = value.strip().lower()

    if len(value) > EMAIL_MAX_LENGTH:
        raise ValueError(
            f"E-mail must have at most {EMAIL_MAX_LENGTH} characters"
        )

    return value


NormalizedEmail = Annotated[EmailStr, AfterValidator(_normalize_email)]

Telephone = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        pattern=r"^[0-9+()\-\s]{8,20}$",
    ),
]


class UserCreate(BaseModel):
    # Unknown fields (for example "role": "ADMIN") are rejected instead of
    # being silently ignored, so mass assignment cannot creep in later.
    model_config = ConfigDict(extra="forbid")

    name: PersonName
    email: NormalizedEmail
    # Upper bound prevents abusing the (deliberately expensive) hash function
    # with enormous passwords.
    password: str = Field(min_length=8, max_length=128)
    telephone: Telephone | None = None
    cpf: str | None = Field(
        default=None,
        pattern=r"^[0-9]{11}$"
    )


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    telephone: str | None = None
    cpf: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: PersonName | None = None
    email: NormalizedEmail | None = None
    telephone: Telephone | None = None
