from backend.app.database import fetch_products, fetch_product_byid
from fastapi import FastAPI, HTTPException
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
    product = fetch_product_byid(id)

    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    return product
        

@app.post("/product")
async def create_product(product: Product):
    new_id = len(products) + 1

    new_product = {
        "id": new_id,
        **product.model_dump()
    }

    products.append(new_product)

    return new_product


@app.put("/products/{id}")
async def up_product(id: int, product: Product):
    for item in products:
        if item["id"] == id:
            item.update(product.model_dump())
            return item
    raise HTTPException(status_code=404, detail="Product not found")   


@app.delete("/products/{id}")
async def delete_product(id: int):
    for item in products:
        if item["id"] == id:
            product_name = item["name"]
            products.remove(item)
            return f"{product_name} deleted"
    raise HTTPException(status_code=404, detail="Product not found")

     

    


