from fastapi import APIRouter, Request, HTTPException, status

from backend.app.schemas.order import OrderCreate, OrderResponse
from backend.app.exceptions import (
    OrderConstraintError,
    ProductNotFoundError,
    InsufficientStockError,
)
from backend.repository.order import post_order

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_order(order_data: OrderCreate, request: Request):
    try:
        order = post_order(
            request.app.state.pool,
            user_id=order_data.user_id,
            address_id=order_data.address_id,
            items=[
                item.model_dump()
                for item in order_data.items
            ],
        )
        return order

    except OrderConstraintError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except ProductNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        ) from exc

    except InsufficientStockError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Insufficient stock for one or more products",
        ) from exc
