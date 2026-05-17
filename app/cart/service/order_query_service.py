from sqlalchemy.orm import Session

from app.cart.data.cart_repository import (
    get_order_by_id_and_operator_id,
    get_orders_by_operator_id,
)
from app.cart.model.cart_schema import OrderListItemResponse, OrderResponse
from app.cart.service.cart_exceptions import CartNotFoundError


def list_orders(
    db: Session,
    operator_id: int,
) -> list[OrderListItemResponse]:
    orders = get_orders_by_operator_id(db=db, operator_id=operator_id)
    return [OrderListItemResponse.model_validate(order) for order in orders]


def get_order_details(
    db: Session,
    operator_id: int,
    order_id: int,
) -> OrderResponse:
    order = get_order_by_id_and_operator_id(
        db=db,
        order_id=order_id,
        operator_id=operator_id,
    )

    if order is None:
        raise CartNotFoundError("Zamówienie nie istnieje.")

    return OrderResponse.model_validate(order)
