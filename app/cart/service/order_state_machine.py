from app.cart.model.order_status import OrderStatus
from app.cart.service.cart_exceptions import CartValidationError

ALLOWED_STATUS_TRANSITIONS = {
    OrderStatus.PENDING: {
        OrderStatus.COMPLETED,
        OrderStatus.CANCELLED,
    },
    OrderStatus.COMPLETED: set(),
    OrderStatus.CANCELLED: set(),
}


def validate_status_transition(
    current_status: str,
    new_status: str,
) -> None:
    allowed_statuses = ALLOWED_STATUS_TRANSITIONS.get(current_status)

    if allowed_statuses is None:
        raise CartValidationError(
            f"Nieznany status zamówienia: {current_status}."
        )

    if new_status not in allowed_statuses:
        raise CartValidationError(
            f"Nie można zmienić statusu zamówienia z {current_status} na {new_status}."
        )
