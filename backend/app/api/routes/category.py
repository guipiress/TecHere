from fastapi import APIRouter, Depends, HTTPException
from psycopg import errors

from backend.app.dependencies import get_pool
from backend.repository.category import (
    fetch_categories,
    fetch_category_by_id,
    post_category,
    put_category,
    del_category
)
from backend.app.schemas.category import (
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate
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


@router.put("/categories/{id}", response_model=CategoryResponse)
async def up_category(
    id: int,
    category: CategoryUpdate,
    pool=Depends(get_pool)
):
    try:
        result = put_category(
            pool,
            id,
            name=category.name
        )

    except errors.UniqueViolation:
        raise HTTPException(
            status_code=409,
            detail="Category already exists"
        )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Category not found"
        )

    return result


@router.delete("/categories/{id}", response_model=CategoryResponse)
async def delete_category(id: int, pool=Depends(get_pool)):
    result = del_category(pool, id)
    if result is None:
        raise HTTPException(status_code=404, detail="Category not found") 
    return result
 