from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from backend.app.schemas.common import INT4_MAX

# Business limits. They bound the work (and the row locks) a single request
# can cause. Adjust to the store's real needs.
MAX_ITEMS_PER_ORDER = 50
MAX_QUANTITY_PER_ITEM = 1000


class OrderItemCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: int = Field(gt=0, le=INT4_MAX)
    quantity: int = Field(gt=0, le=MAX_QUANTITY_PER_ITEM)


class OrderCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # NOTE: once authentication exists, user_id must come from the
    # authenticated session, never from the request body.
    user_id: int = Field(gt=0, le=INT4_MAX)
    address_id: int = Field(gt=0, le=INT4_MAX)
    items: list[OrderItemCreate] = Field(
        min_length=1,
        max_length=MAX_ITEMS_PER_ORDER,
    )


class OrderItemResponse(BaseModel):
    id: int
    order_id: int
    product_id: int
    quantity: int
    unit_price: Decimal


class OrderResponse(BaseModel):
    id: int
    user_id: int
    address_id: int
    status: str
    total_price: Decimal
    created_at: datetime
    items: list[OrderItemResponse]


class OrderStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str = Field(
        pattern="^(PENDING|PAID|CANCELLED)$"
    )
