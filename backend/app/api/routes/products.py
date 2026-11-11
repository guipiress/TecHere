from fastapi import APIRouter, Depends, HTTPException, Query

from backend.app.dependencies import get_pool
from backend.repository.product import (
    fetch_products,
    fetch_product_by_id,
    post_product,
    put_product,
    del_product
)

from backend.app.schemas.product import (
    ProductResponse,
    ProductCreate,
    ProductUpdate
)
from backend.app.exceptions import (
    CategoryNotFoundError,
    ProductConstraintError
)

router = APIRouter()


@router.get("/products", response_model=list[ProductResponse])
def get_products(
    pool=Depends(get_pool),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    return fetch_products(pool, limit, offset)


@router.get("/products/{id}", response_model=ProductResponse)
def get_product(id: int, pool=Depends(get_pool)):
    product = fetch_product_by_id(id, pool)

    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    return product


@router.post("/products", status_code=201, response_model=ProductResponse)
def create_product(
    product: ProductCreate,
    pool=Depends(get_pool)
):
    try:
        new_product = post_product(
            pool,
            name=product.name,
            purchase_price=product.purchase_price,
            sale_price=product.sale_price,
            stock=product.stock,
            brand=product.brand,
            category_id=product.category_id,
            description=product.description
        )

    except CategoryNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Category not found"
        )

    except ProductConstraintError:
        raise HTTPException(
            status_code=400,
            detail="Product violates database constraints"
        )

    return new_product
    


@router.put("/products/{id}", response_model=ProductResponse)
def up_product(
    id: int,
    product: ProductUpdate,
    pool=Depends(get_pool)
):
    data = product.model_dump(exclude_unset=True)

    if not data:
        raise HTTPException(
            status_code=400,
            detail="At least one field must be provided"
        )

    # Only "description" is nullable in the database. An explicit null for any
    # other field would otherwise hit a NOT NULL constraint.
    null_fields = [
        field for field, value in data.items()
        if value is None and field != "description"
    ]

    if null_fields:
        raise HTTPException(
            status_code=422,
            detail="Fields cannot be null: " + ", ".join(sorted(null_fields))
        )

    try:
        result = put_product(pool, id, **data)

    except CategoryNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Category not found"
        )

    except ProductConstraintError:
        raise HTTPException(
            status_code=400,
            detail="Product violates database constraints"
        )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    return result



@router.delete("/products/{id}", response_model=ProductResponse)
def delete_product(id: int, pool=Depends(get_pool)):
    result = del_product(pool, id)

    if result is None:
        raise HTTPException(status_code=404, detail="Product not found")

    return result
