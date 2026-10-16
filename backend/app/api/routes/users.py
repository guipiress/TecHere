from fastapi import APIRouter, Depends, HTTPException

from backend.app.dependencies import get_pool
from backend.app.security import hash_password
from backend.app.exceptions import (
    UserEmailAlreadyExistsError,
    UserCPFAlreadyExistsError,
)
from backend.app.schemas.users import UserCreate, UserResponse
from backend.repository.user import post_user

router = APIRouter()


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