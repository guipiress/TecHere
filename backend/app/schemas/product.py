from pydantic import BaseModel
from decimal import Decimal

class ProductCreate(BaseModel):
    name: str
    purchase_price: Decimal 
    sale_price: Decimal 
    stock: int
    brand: str
    category_id: int
    description: str | None = None

class ProductUpdate(BaseModel):
    name: str
    purchase_price: Decimal
    sale_price: Decimal
    stock: int
    brand: str
    category_id: int
    description: str | None = None

class ProductResponse(BaseModel):
    id : int
    name: str
    purchase_price: Decimal
    sale_price: Decimal
    stock: int
    brand: str
    category_id: int
    description: str | None = None

