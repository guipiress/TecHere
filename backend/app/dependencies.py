from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError

from backend.app.security import decode_access_token
from backend.repository.user import fetch_user_by_id


bearer_scheme = HTTPBearer(auto_error=False)


def get_pool(request: Request):
    return request.app.state.pool


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    pool=Depends(get_pool),
):
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não autenticado.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise unauthorized

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = payload.get("sub")

        if (
            not isinstance(user_id, str)
            or not user_id.isdecimal()
            or int(user_id) <= 0
        ):
            raise unauthorized

        user = fetch_user_by_id(int(user_id), pool)

    except (InvalidTokenError, ValueError):
        raise unauthorized

    if user is None or not user["is_active"]:
        raise unauthorized

    return user


STAFF_ROLES = ("ADMIN", "EMPLOYEE")


def is_staff(user) -> bool:
    return user["role"] in STAFF_ROLES


def ensure_self_or_roles(current_user, target_user_id: int, *roles):
    """Allow the owner of the resource, or any of the given roles."""
    if current_user["id"] == target_user_id:
        return

    if current_user["role"] in roles:
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Permission denied.",
    )


def require_roles(*allowed_roles):
    def role_checker(current_user=Depends(get_current_user)):
        if current_user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied.",
            )

        return current_user

    return role_checker


# Shared by the route modules. Staff manage the catalog; deleting things and
# reading other people's personal data is limited to administrators.
require_staff = require_roles(*STAFF_ROLES)
require_admin = require_roles("ADMIN")
