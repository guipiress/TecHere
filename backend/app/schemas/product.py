from pydantic import BaseModel, Field
from decimal import Decimal

class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    purchase_price: Decimal = Field(ge=0)
    sale_price: Decimal = Field(ge=0)
    stock: int = Field(ge=0)
    brand: str = Field(min_length=1, max_length=100)
    category_id: int = Field(gt=0)
    description: str | None = Field(default=None, max_length=500)

class ProductUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    purchase_price: Decimal = Field(ge=0)
    sale_price: Decimal = Field(ge=0)
    stock: int = Field(ge=0)
    brand: str = Field(min_length=1, max_length=100)
    category_id: int = Field(gt=0)
    description: str | None = Field(default=None, max_length=500)

class ProductResponse(BaseModel):
    id : int
    name: str
    purchase_price: Decimal
    sale_price: Decimal
    stock: int
    brand: str
    category_id: int
    description: str | None = None

