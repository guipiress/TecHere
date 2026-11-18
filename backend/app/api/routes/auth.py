from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.dependencies import get_pool
from backend.app.schemas.auth import LoginRequest, TokenResponse
from backend.app.security import verify_password, create_access_token
from backend.repository.user import fetch_user_by_email_for_auth


router = APIRouter()


@router.post("/auth/login", response_model=TokenResponse)
def login(credentials: LoginRequest, pool=Depends(get_pool)):
    user = fetch_user_by_email_for_auth(
        pool,
        str(credentials.email),
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha inválidos.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    password_valid = verify_password(
        credentials.password,
        user["password_hash"],
    )

    if not password_valid or not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha inválidos.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        {"sub": str(user["id"])}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }
