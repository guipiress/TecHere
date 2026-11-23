import hashlib
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status

from backend.app.dependencies import get_pool
from backend.app.rate_limit import login_account_limiter, login_ip_limiter
from backend.app.schemas.auth import LoginRequest, TokenResponse
from backend.app.security import (
    create_access_token,
    verify_password,
    verify_password_against_dummy,
)
from backend.repository.user import fetch_user_by_email_for_auth


logger = logging.getLogger("techere.auth")

router = APIRouter()


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _fingerprint(email: str) -> str:
    # Lets an operator correlate repeated attempts without writing the
    # e-mail address (personal data) to the logs.
    return hashlib.sha256(email.encode("utf-8")).hexdigest()[:12]


def _invalid_credentials() -> HTTPException:
    # One message and one status for every failure (unknown e-mail, wrong
    # password, inactive account) so the response reveals nothing.
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="E-mail ou senha inválidos.",
        headers={"WWW-Authenticate": "Bearer"},
    )


@router.post("/auth/login", response_model=TokenResponse)
def login(
    credentials: LoginRequest,
    request: Request,
    pool=Depends(get_pool),
):
    email = str(credentials.email)
    ip = _client_ip(request)
    account_key = f"{ip}|{email}"

    # Checked before touching the database or the (expensive) hash function.
    retry_after = max(
        login_ip_limiter.retry_after(ip),
        login_account_limiter.retry_after(account_key),
    )

    if retry_after:
        logger.warning(
            "login blocked by rate limit ip=%s account=%s",
            ip,
            _fingerprint(email),
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Muitas tentativas. Tente novamente mais tarde.",
            headers={"Retry-After": str(retry_after)},
        )

    user = fetch_user_by_email_for_auth(pool, email)

    if user is None:
        # Same cost as a real check, so response time does not reveal
        # whether the e-mail is registered.
        password_valid = verify_password_against_dummy(credentials.password)
    else:
        password_valid = verify_password(
            credentials.password,
            user["password_hash"],
        )

    if user is None or not password_valid or not user["is_active"]:
        login_ip_limiter.record(ip)
        login_account_limiter.record(account_key)
        logger.warning(
            "failed login ip=%s account=%s",
            ip,
            _fingerprint(email),
        )
        raise _invalid_credentials()

    login_account_limiter.reset(account_key)

    access_token = create_access_token(
        {"sub": str(user["id"])}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }
