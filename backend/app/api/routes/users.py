from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi import Query
from backend.app.dependencies import (
    ensure_self_or_roles,
    get_current_user,
    get_pool,
    require_admin,
)
from backend.app.rate_limit import register_ip_limiter
from backend.app.security import hash_password
from backend.app.exceptions import (
    UserEmailAlreadyExistsError,
    UserCPFAlreadyExistsError,
)
from backend.app.schemas.users import UserCreate, UserResponse, UserUpdate
from backend.repository.user import post_user, fetch_user_by_id, fetch_users, put_user, delete_user

router = APIRouter()



@router.get("/users", response_model=list[UserResponse])
def get_users(
    pool=Depends(get_pool),
    _admin=Depends(require_admin),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    users = fetch_users(pool, limit, offset)
    return users


# Declared before /users/{id}, otherwise "me" would be parsed as the {id}.
@router.get("/users/me", response_model=UserResponse)
def get_me(current_user=Depends(get_current_user)):
    return current_user


@router.get("/users/{id}", response_model=UserResponse)
def get_user_by_id(
    id: int,
    pool=Depends(get_pool),
    current_user=Depends(get_current_user),
):
    ensure_self_or_roles(current_user, id, "ADMIN")

    user = fetch_user_by_id(id,pool)

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.post("/users", status_code=201, response_model=UserResponse)
def create_user(
    user: UserCreate,
    request: Request,
    pool=Depends(get_pool),
):
    ip = request.client.host if request.client else "unknown"
    retry_after = register_ip_limiter.retry_after(ip)

    if retry_after:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Muitos cadastros deste endereço. Tente mais tarde.",
            headers={"Retry-After": str(retry_after)},
        )

    register_ip_limiter.record(ip)

    password_hash = hash_password(user.password)

    try:
        new_user = post_user(
            pool,
            name=user.name,
            email=str(user.email),
            password_hash=password_hash,
            telephone=user.telephone,
            cpf=user.cpf,
        )

    except UserEmailAlreadyExistsError:
        raise HTTPException(
            status_code=409,
            detail="Este e-mail já está cadastrado.",
        )

    except UserCPFAlreadyExistsError:
        raise HTTPException(
            status_code=409,
            detail="Este CPF já está cadastrado.",
        )

    return new_user


@router.put("/users/{id}", response_model=UserResponse)
def update_user(
    id: int,
    user: UserUpdate,
    pool=Depends(get_pool),
    current_user=Depends(get_current_user),
):
    ensure_self_or_roles(current_user, id, "ADMIN")

    data = user.model_dump(exclude_unset=True)

    # The e-mail is the login. Changing it from a session (which may be a
    # stolen token) would hand the account over, so until there is an e-mail
    # verification / re-authentication flow only an administrator may do it.
    if "email" in data and current_user["role"] != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Somente administradores podem alterar o e-mail.",
        )

    if not data:
        raise HTTPException(
            status_code=422,
            detail="Informe pelo menos um campo para atualizar.",
        )

    if "name" in data and data["name"] is None:
        raise HTTPException(
            status_code=422,
            detail="O nome não pode ser nulo.",
        )

    if "email" in data and data["email"] is None:
        raise HTTPException(
            status_code=422,
            detail="O e-mail não pode ser nulo.",
        )

    try:
        updated_user = put_user(pool, id, data)
    except UserEmailAlreadyExistsError:
        raise HTTPException(
            status_code=409,
            detail="Este e-mail já está cadastrado.",
        )

    if updated_user is None:
        raise HTTPException(
            status_code=404,
            detail="Usuário não encontrado.",
        )

    return updated_user


@router.delete("/users/{id}", status_code=status.HTTP_200_OK)
def remove_user(
    id: int,
    pool=Depends(get_pool),
    _admin=Depends(require_admin),
):
    deleted_user = delete_user(pool, id)

    if deleted_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado.",
        )

    return {
        "message": "Usuário excluído com sucesso.",
        "user": deleted_user,
    }