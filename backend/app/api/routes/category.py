from fastapi import APIRouter, Depends, HTTPException
from psycopg import errors

from backend.app.dependencies import get_pool
from backend.database.category import (
    fetch_categories,
    fetch_category_by_id,
    post_category
)
from backend.app.schemas.category import (
    CategoryCreate,
    CategoryResponse
)

router = APIRouter()


@router.get("/categories", response_model=list[CategoryResponse])
async def get_categories(pool=Depends(get_pool)):
    return fetch_categories(pool)


@router.get("/categories/{id}", response_model=CategoryResponse)
async def get_category(id: int, pool=Depends(get_pool)):
    category = fetch_category_by_id(id, pool)

    if category is None:
        raise HTTPException(
            status_code=404,
            detail="Category not found"
        )

    return category


@router.post(
    "/categories",
    status_code=201,
    response_model=CategoryResponse
)
async def create_category(
    category: CategoryCreate,
    pool=Depends(get_pool)
):
    try:
        return post_category(
            pool,
            name=category.name
        )

    except errors.UniqueViolation:
        raise HTTPException(
            status_code=409,
            detail="Category already exists"
        )