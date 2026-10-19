from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    email: EmailStr
    password: str = Field(min_length=8)
    telephone: str | None = Field(default=None, max_length=20)
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
    name: str | None = Field(default=None, min_length=1, max_length=150)
    email: EmailStr | None = None
    telephone: str | None = Field(default=None, max_length=20)