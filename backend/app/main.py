from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from decimal import Decimal

class Product(BaseModel):
        name: str
        purchase_price: Decimal
        sale_price: Decimal


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
    return products

@app.get("/products/{id}")
async def get_product(id: int):
    for product in products:
        if product["id"] == id:
            return product
            
    raise HTTPException(status_code=404, detail="Product not found")

@app.post("/product")
async def create_product(product: Product):
    new_id = len(products) + 1

    new_product = {
        "id": new_id,
        **product.model_dump()
    }

    products.append(new_product)

    return new_product


    


