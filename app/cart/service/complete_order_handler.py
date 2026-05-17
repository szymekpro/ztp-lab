from sqlalchemy.orm import Session

from app.cart.data.cart_repository import (
    add_processed_command,
    get_order_by_id_and_operator_id,
    is_command_already_processed,
    save_order,
)
from app.cart.model.cart_schema import OrderResponse
from app.cart.model.order_status import OrderStatus
from app.cart.service.cart_exceptions import CartNotFoundError, CartValidationError
from app.cart.service.complete_order_command import CompleteOrderCommand
from app.cart.service.order_notification_service import create_order_completed_notifications
from app.cart.service.order_state_machine import validate_status_transition


def handle_complete_order(
    db: Session,
    command: CompleteOrderCommand,
) -> OrderResponse:
    if is_command_already_processed(
        db=db,
        command_name=command.command_name,
        idempotency_key=command.idempotency_key,
    ):
        order = get_order_by_id_and_operator_id(
            db=db,
            order_id=command.order_id,
            operator_id=command.operator_id,
        )

        if order is None:
            raise CartNotFoundError("Zamówienie nie istnieje.")

        return OrderResponse.model_validate(order)

    order = get_order_by_id_and_operator_id(
        db=db,
        order_id=command.order_id,
        operator_id=command.operator_id,
    )

    if order is None:
        raise CartNotFoundError("Zamówienie nie istnieje.")

    validate_status_transition(
        current_status=order.status,
        new_status=OrderStatus.COMPLETED,
    )

    order.status = OrderStatus.COMPLETED
    order = save_order(db, order)

    add_processed_command(
        db=db,
        command_name=command.command_name,
        idempotency_key=command.idempotency_key,
        operator_id=command.operator_id,
    )

    create_order_completed_notifications(
        db=db,
        order=order,
        operator_email=command.completed_by,
        notify_email=command.notify_email,
        notify_push=command.notify_push,
    )

    return OrderResponse.model_validate(order)
