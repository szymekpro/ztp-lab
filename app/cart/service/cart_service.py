from datetime import datetime
from sqlalchemy.orm import Session

from app.REST.data.product_repository import get_product_by_id
from app.cart.data.cart_repository import (
    add_cart_item,
    delete_cart_item,
    get_cart_item_by_cart_and_product,
    get_cart_item_by_id,
    get_or_create_cart,
    get_order_by_id_and_operator_id,
    get_orders_by_operator_id,
    update_cart_item_quantity,
)
from app.cart.model.cart_draft_orm import CartDraftORM
from app.cart.model.cart_schema import (
    CartDraftItemResponse,
    CartDraftResponse,
    CartItemCreate,
    CartItemUpdate,
    OrderListItemResponse,
    OrderResponse,
)
from app.cart.service.cart_exceptions import (
    CartConflictError,
    CartNotFoundError,
    CartValidationError,
)


def _calculate_total_price(cart: CartDraftORM) -> float:
    total = 0.0
    for item in cart.items:
        if item.product is not None:
            total += float(item.product.price) * item.quantity
    return total


def _build_cart_response(cart: CartDraftORM) -> CartDraftResponse:
    return CartDraftResponse(
        id=cart.id,
        operator_id=cart.operator_id,
        items=[
            CartDraftItemResponse.model_validate(item)
            for item in cart.items
        ],
        items_count=len(cart.items),
        total_price=_calculate_total_price(cart),
        created_at=cart.created_at,
        updated_at=cart.updated_at,
    )


def get_current_cart(
    db: Session,
    operator_id: int,
) -> CartDraftResponse:
    cart = get_or_create_cart(db, operator_id)
    return _build_cart_response(cart)


def add_product_to_cart(
    db: Session,
    operator_id: int,
    payload: CartItemCreate,
) -> CartDraftResponse:
    cart = get_or_create_cart(db, operator_id)

    product = get_product_by_id(db, payload.product_id)
    if product is None:
        raise CartNotFoundError("Produkt o podanym identyfikatorze nie istnieje.")

    if payload.quantity > product.quantity:
        raise CartValidationError(
            f"Żądana ilość ({payload.quantity}) przekracza dostępny stan magazynowy ({product.quantity})."
        )

    existing_item = get_cart_item_by_cart_and_product(
        db=db,
        cart_id=cart.id,
        product_id=payload.product_id,
    )
    if existing_item is not None:
        raise CartConflictError("Ten produkt jest już w koszyku. Użyj PATCH, aby zmienić ilość.")

    add_cart_item(
        db=db,
        cart_id=cart.id,
        product_id=payload.product_id,
        quantity=payload.quantity,
    )

    cart.updated_at = datetime.now()
    db.add(cart)
    db.commit()

    refreshed_cart = get_or_create_cart(db, operator_id)
    return _build_cart_response(refreshed_cart)


def update_cart_item(
    db: Session,
    operator_id: int,
    item_id: int,
    payload: CartItemUpdate,
) -> CartDraftResponse:
    cart = get_or_create_cart(db, operator_id)

    item = get_cart_item_by_id(db, item_id)
    if item is None:
        raise CartNotFoundError("Pozycja koszyka nie istnieje.")

    if item.cart_id != cart.id:
        raise CartNotFoundError("Pozycja nie należy do koszyka aktualnego operatora.")

    product = get_product_by_id(db, item.product_id)
    if product is None:
        raise CartNotFoundError("Produkt powiązany z pozycją nie istnieje.")

    if payload.quantity > product.quantity:
        raise CartValidationError(
            f"Żądana ilość ({payload.quantity}) przekracza dostępny stan magazynowy ({product.quantity})."
        )

    update_cart_item_quantity(db, item, payload.quantity)

    cart.updated_at = datetime.now()
    db.add(cart)
    db.commit()

    refreshed_cart = get_or_create_cart(db, operator_id)
    return _build_cart_response(refreshed_cart)


def remove_product_from_cart(
    db: Session,
    operator_id: int,
    item_id: int,
) -> None:
    cart = get_or_create_cart(db, operator_id)

    item = get_cart_item_by_id(db, item_id)
    if item is None:
        raise CartNotFoundError("Pozycja koszyka nie istnieje.")

    if item.cart_id != cart.id:
        raise CartNotFoundError("Pozycja nie należy do koszyka aktualnego operatora.")

    delete_cart_item(db, item)

    cart.updated_at = datetime.now()
    db.add(cart)
    db.commit()


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
