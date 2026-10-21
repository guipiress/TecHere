from fastapi import APIRouter, Depends, HTTPException, status
from fastapi import Query
from backend.app.dependencies import get_pool
from backend.app.security import hash_password
from backend.app.exceptions import (
    UserEmailAlreadyExistsError,
    UserCPFAlreadyExistsError,
)
from backend.app.schemas.users import UserCreate, UserResponse, UserUpdate
from backend.repository.user import post_user, fetch_user_by_id, fetch_users, put_user, delete_user

router = APIRouter()



@router.get("/users", response_model=list[UserResponse])
async def get_users(
    pool=Depends(get_pool),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    users = fetch_users(pool, limit, offset)
    return users


@router.get("/users/{id}", response_model=UserResponse)
async def get_user_by_id(id: int, pool=Depends(get_pool)):
    user = fetch_user_by_id(id,pool)

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.post("/users", status_code=201, response_model=UserResponse)
async def create_user(
    user: UserCreate,
    pool=Depends(get_pool),
):
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
async def update_user(
    id: int,
    user: UserUpdate,
    pool=Depends(get_pool),
):
    data = user.model_dump(exclude_unset=True)

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
async def remove_user(
    id: int,
    pool=Depends(get_pool),
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