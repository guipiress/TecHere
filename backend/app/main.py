from fastapi import FastAPI, HTTPException
from backend.app.api.routes.products import router
from backend.app.database import post_product, put_product, del_product
from backend.app.schemas.product import ProductResponse, ProductCreate, ProductUpdate


app = FastAPI()

app.include_router(router)



@app.get("/")
async def root():
    return "Store"

        

@app.post("/products", status_code=201, response_model=ProductResponse)
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



@app.put("/products/{id}", response_model=ProductResponse)
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



@app.delete("/products/{id}", response_model=ProductResponse)
async def delete_product(id: int):

    result = del_product(id)

    if result is None:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return result


    
    
     

    


