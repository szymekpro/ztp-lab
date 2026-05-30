from sqlalchemy.orm import Session

from app.cart.data.cart_repository import get_orders_by_operator_id
from app.cart.model.cart_schema import OrderListItemResponse
from app.cart.model.order_status import OrderStatus


def get_dashboard_summary(
    db: Session,
    operator_id: int,
) -> dict:
    orders = get_orders_by_operator_id(
        db=db,
        operator_id=operator_id,
    )

    total_orders = len(orders)

    pending_orders = len(
        [order for order in orders if order.status == OrderStatus.PENDING]
    )

    completed_orders = len(
        [order for order in orders if order.status == OrderStatus.COMPLETED]
    )

    cancelled_orders = len(
        [order for order in orders if order.status == OrderStatus.CANCELLED]
    )

    last_order = orders[0] if orders else None
    last_order_payload = (
        OrderListItemResponse.model_validate(last_order) if last_order else None
    )

    return {
        "total_orders": total_orders,
        "pending_orders": pending_orders,
        "completed_orders": completed_orders,
        "cancelled_orders": cancelled_orders,
        "last_order": last_order_payload,
    }
