from fastapi import APIRouter, Depends, HTTPException
from backend.app.dependencies import get_pool
from backend.app.database import fetch_products, fetch_product_by_id, post_product, put_product, del_product
from backend.app.schemas.product import ProductResponse, ProductCreate, ProductUpdate
from backend.app.exceptions import CategoryNotFoundError, ProductConstraintError

router = APIRouter()


@router.get("/products", response_model=list[ProductResponse])
async def get_products(pool = Depends(get_pool)):
    return fetch_products(pool)


@router.get("/products/{id}", response_model=ProductResponse)
async def get_product(id: int, pool=Depends(get_pool)):
    product = fetch_product_by_id(id, pool)

    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    return product
        

@router.post("/products", status_code=201, response_model=ProductResponse)
async def create_product(
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


@router.post("/categories")
async def create_category(category: CategoryCreate, pool=Depends(get_pool)):

    try:
        return create_category(
            pool,
            name=category.name
        )

    except errors.UniqueViolation:
        raise HTTPException(
            status_code=409,
            detail="Category already exists"
        )


@router.put("/products/{id}", response_model=ProductResponse)
async def up_product(
    id: int,
    product: ProductUpdate,
    pool=Depends(get_pool)
):
    result = put_product(
        pool,
        id,
        name=product.name,
        purchase_price=product.purchase_price,
        sale_price=product.sale_price,
        stock=product.stock,
        brand=product.brand,
        category_id=product.category_id,
        description=product.description
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    return result


@router.delete("/products/{id}", response_model=ProductResponse)
async def delete_product(id: int, pool=Depends(get_pool)):
    result = del_product(pool, id)

    if result is None:
        raise HTTPException(status_code=404, detail="Product not found")

    return result
