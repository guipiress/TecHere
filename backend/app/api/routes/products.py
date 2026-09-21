from fastapi import APIRouter, HTTPException
from backend.app.database import fetch_products, fetch_product_by_id
from backend.app.schemas.product import ProductResponse


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
        
