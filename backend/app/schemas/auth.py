from pydantic import BaseModel, ConfigDict, Field

from backend.app.schemas.users import NormalizedEmail


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: NormalizedEmail
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
