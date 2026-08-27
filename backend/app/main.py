from backend.app.database import fetch_products, fetch_product_by_id, post_product, put_product
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from decimal import Decimal

class Product(BaseModel):
    name: str
    purchase_price: Decimal
    sale_price: Decimal
    stock: int
    brand: str
    category_id: int
    description: str


app = FastAPI()

products = [
    {"id": 1, "name": "Notebook"},
    {"id": 2, "name": "Mouse"},
    {"id": 3, "name": "Teclado"}
]


@app.get("/")
async def root():
    return "Store"


@app.get("/products")
async def get_products():
    return fetch_products()


@app.get("/products/{id}")
async def get_product(id: int):
    product = fetch_product_by_id(id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    return product
        

@app.post("/products", status_code=201)
async def create_product(product: Product):
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


@app.put("/products/{id}")
async def up_product(id: int, product: Product):
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
    return product


@app.delete("/products/{id}")
async def delete_product(id: int):
    for item in products:
        if item["id"] == id:
            product_name = item["name"]
            products.remove(item)
            return f"{product_name} deleted"
    raise HTTPException(status_code=404, detail="Product not found")

     

    


