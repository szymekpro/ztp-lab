from datetime import datetime

from sqlalchemy.orm import Session

from app.REST.data.product_repository import get_product_by_id, save_product
from app.cart.data.cart_repository import (
    add_order,
    add_order_item,
    clear_cart_items,
    get_or_create_cart,
)
from app.cart.model.cart_draft_orm import CartDraftORM
from app.cart.model.order_item_orm import OrderItemORM
from app.cart.model.order_orm import OrderORM
from app.cart.model.cart_schema import OrderResponse
from app.cart.service.cart_exceptions import CartValidationError
from app.cart.service.checkout_command import CheckoutCommand


def _generate_order_number(order_id: int) -> str:
    today = datetime.now().strftime("%Y%m%d")
    return f"ZAM-{today}-{order_id:06d}"


def _get_valid_cart(
    db: Session,
    operator_id: int,
) -> CartDraftORM:
    cart = get_or_create_cart(db, operator_id)

    if not cart.items:
        raise CartValidationError("Nie można złożyć zamówienia z pustego koszyka.")

    return cart


def _calculate_items_count(cart: CartDraftORM) -> int:
    return len(cart.items)


def _calculate_total_price(cart: CartDraftORM) -> float:
    return sum(float(item.product.price) * item.quantity for item in cart.items)


def _create_order(
    db: Session,
    operator_id: int,
    items_count: int,
    total_price: float,
) -> OrderORM:
    order = OrderORM(
        operator_id=operator_id,
        order_number="TEMP",
        status="PENDING",
        items_count=items_count,
        total_price=total_price,
    )

    order = add_order(db, order)

    order.order_number = _generate_order_number(order.id)
    db.add(order)
    db.commit()
    db.refresh(order)

    return order


def _create_order_items(
    db: Session,
    order_id: int,
    cart: CartDraftORM,
) -> None:
    for item in cart.items:
        product = item.product

        order_item = OrderItemORM(
            order_id=order_id,
            product_id=product.id,
            product_name=product.name,
            product_price=float(product.price),
            quantity=item.quantity,
        )

        add_order_item(db, order_item)

        product.quantity -= item.quantity
        save_product(db, product)


def _build_order_response(order: OrderORM) -> OrderResponse:
    return OrderResponse(
        id=order.id,
        operator_id=order.operator_id,
        order_number=order.order_number,
        status=order.status,
        items_count=order.items_count,
        total_price=float(order.total_price),
        created_at=order.created_at,
        items=order.items,
    )


def handle_checkout(
    db: Session,
    command: CheckoutCommand,
) -> OrderResponse:
    cart = _get_valid_cart(db, command.operator_id)

    for item in cart.items:
        product = get_product_by_id(db, item.product_id)
        if product is None:
            raise CartValidationError(f"Produkt o ID {item.product_id} nie istnieje.")
        if item.quantity > product.quantity:
            raise CartValidationError(
                f"Niewystarczający stan magazynowy dla produktu '{product.name}'. "
                f"Dostępne: {product.quantity}, zamówione: {item.quantity}."
            )

    items_count = _calculate_items_count(cart)
    total_price = _calculate_total_price(cart)

    order = _create_order(
        db=db,
        operator_id=command.operator_id,
        items_count=items_count,
        total_price=total_price,
    )

    _create_order_items(db=db, order_id=order.id, cart=cart)

    clear_cart_items(db, cart.id)

    db.refresh(order)
    return _build_order_response(order)
