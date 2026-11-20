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
