from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.app.dependencies import get_pool

from backend.app.schemas.order import OrderCreate, OrderResponse, OrderStatusUpdate
from backend.app.exceptions import (
    OrderConstraintError,
    ProductNotFoundError,
    InsufficientStockError,
    OrderNotFoundError,
)
from backend.repository.order import post_order, fetch_orders, fetch_order_by_id, update_order_status

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_order(order_data: OrderCreate, pool=Depends(get_pool)):
    try:
        order = post_order(
            pool,
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



@router.get("", response_model=list[OrderResponse])
def get_orders(
    pool=Depends(get_pool),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    orders = fetch_orders(pool, limit, offset)
    return orders


@router.get("/{order_id}", response_model=OrderResponse)
def get_order_by_id(order_id: int, pool=Depends(get_pool)):
    try:
        order = fetch_order_by_id(
            pool,
            order_id,
        )
        return order

    except OrderNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail="Order not found",
        ) from exc



@router.put("/{order_id}/status", response_model=OrderResponse)
def change_order_status(
    order_id: int,
    status_data: OrderStatusUpdate,
    pool=Depends(get_pool),
):
    try:
        return update_order_status(
            pool,
            order_id,
            status_data.status,
        )

    except OrderNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail="Order not found",
        ) from exc

    except OrderConstraintError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc