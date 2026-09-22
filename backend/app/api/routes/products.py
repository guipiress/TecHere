from fastapi import APIRouter, HTTPException
from backend.app.database import fetch_products, fetch_product_by_id, post_product, put_product, del_product
from backend.app.schemas.product import ProductResponse, ProductCreate, ProductUpdate


router = APIRouter()


@router.get("/products", response_model=list[ProductResponse])
async def get_products():
    return fetch_products()


@router.get("/products/{id}", response_model=ProductResponse)
async def get_product(id: int):
    product = fetch_product_by_id(id)

    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    return product
        

@router.post("/products", status_code=201, response_model=ProductResponse)
async def create_product(product: ProductCreate):
    new_product = post_product(
        product.name,
        product.purchase_price,
        product.sale_price,
        product.stock,
        product.brand,
        product.category_id,
        product.description
    )

    return new_product


@router.put("/products/{id}", response_model=ProductResponse)
async def up_product(id: int, product: ProductUpdate):
    result = put_product(
        id,
        product.name,
        product.purchase_price,
        product.sale_price,
        product.stock,
        product.brand,
        product.category_id,
        product.description
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return result


@router.delete("/products/{id}", response_model=ProductResponse)
async def delete_product(id: int):

    result = del_product(id)

    if result is None:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return result