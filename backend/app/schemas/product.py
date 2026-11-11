from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from backend.app.schemas.common import (
    INT4_MAX,
    Brand,
    Description,
    ProductName,
)

# NUMERIC(10,2): at most 8 integer digits and exactly 2 decimals. Without
# these bounds PostgreSQL either raises "numeric field overflow" (HTTP 500)
# or silently rounds (10.999 would be stored as 11.00).
Money = Annotated[Decimal, Field(ge=0, max_digits=10, decimal_places=2)]


class ProductCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: ProductName
    purchase_price: Money
    sale_price: Money
    stock: int = Field(ge=0, le=INT4_MAX)
    brand: Brand
    category_id: int = Field(gt=0, le=INT4_MAX)
    description: Description | None = None


class ProductUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: ProductName | None = None
    purchase_price: Money | None = None
    sale_price: Money | None = None
    stock: int | None = Field(default=None, ge=0, le=INT4_MAX)
    brand: Brand | None = None
    category_id: int | None = Field(default=None, gt=0, le=INT4_MAX)
    description: Description | None = None


class ProductResponse(BaseModel):
    id: int
    name: str
    purchase_price: Decimal
    sale_price: Decimal
    stock: int
    brand: str
    category_id: int
    category_name: str
    description: str | None = None
