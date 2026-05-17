from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.REST.data.database import get_db
from app.identity.model.operator_orm import OperatorORM
from app.identity.service.auth_exceptions import AuthorizationError
from app.identity.service.auth_service import get_current_operator
from app.cart.model.cart_schema import (
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
from app.cart.service.cart_service import (
    add_product_to_cart,
    get_current_cart,
    remove_product_from_cart,
    update_cart_item,
)
from app.cart.service.checkout_command import CheckoutCommand
from app.cart.service.checkout_handler import handle_checkout
from app.cart.service.order_query_service import get_order_details, list_orders
from app.cart.service.complete_order_command import CompleteOrderCommand
from app.cart.service.complete_order_handler import handle_complete_order


router = APIRouter(
    prefix="/cart",
    tags=["Cart"],
)

orders_router = APIRouter(
    prefix="/orders",
    tags=["Orders"],
)


def get_current_operator_dependency(
    auth_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> OperatorORM:
    if auth_token is None:
        raise HTTPException(status_code=401, detail="Brak aktywnej sesji.")

    try:
        return get_current_operator(db, auth_token)

    except AuthorizationError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get(
    "",
    response_model=CartDraftResponse,
    status_code=status.HTTP_200_OK,
)
def get_cart_endpoint(
    operator: OperatorORM = Depends(get_current_operator_dependency),
    db: Session = Depends(get_db),
):
    return get_current_cart(db=db, operator_id=operator.id)


@router.post(
    "/items",
    response_model=CartDraftResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_cart_item_endpoint(
    payload: CartItemCreate,
    operator: OperatorORM = Depends(get_current_operator_dependency),
    db: Session = Depends(get_db),
):
    try:
        return add_product_to_cart(
            db=db,
            operator_id=operator.id,
            payload=payload,
        )

    except CartNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    except CartValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))

    except CartConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.patch(
    "/items/{item_id}",
    response_model=CartDraftResponse,
    status_code=status.HTTP_200_OK,
)
def update_cart_item_endpoint(
    payload: CartItemUpdate,
    item_id: int = Path(..., gt=0),
    operator: OperatorORM = Depends(get_current_operator_dependency),
    db: Session = Depends(get_db),
):
    try:
        return update_cart_item(
            db=db,
            operator_id=operator.id,
            item_id=item_id,
            payload=payload,
        )

    except CartNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    except CartValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.delete(
    "/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_cart_item_endpoint(
    item_id: int = Path(..., gt=0),
    operator: OperatorORM = Depends(get_current_operator_dependency),
    db: Session = Depends(get_db),
):
    try:
        remove_product_from_cart(
            db=db,
            operator_id=operator.id,
            item_id=item_id,
        )
        return

    except CartNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/checkout",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
)
def checkout_endpoint(
    operator: OperatorORM = Depends(get_current_operator_dependency),
    db: Session = Depends(get_db),
):
    command = CheckoutCommand(operator_id=operator.id)

    try:
        return handle_checkout(db=db, command=command)

    except CartValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@orders_router.get(
    "",
    response_model=list[OrderListItemResponse],
    status_code=status.HTTP_200_OK,
)
def list_orders_endpoint(
    operator: OperatorORM = Depends(get_current_operator_dependency),
    db: Session = Depends(get_db),
):
    return list_orders(db=db, operator_id=operator.id)


@orders_router.get(
    "/{order_id}",
    response_model=OrderResponse,
    status_code=status.HTTP_200_OK,
)
def get_order_details_endpoint(
    order_id: int = Path(..., gt=0),
    operator: OperatorORM = Depends(get_current_operator_dependency),
    db: Session = Depends(get_db),
):
    try:
        return get_order_details(
            db=db,
            operator_id=operator.id,
            order_id=order_id,
        )

    except CartNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@orders_router.post(
    "/{order_id}/complete",
    response_model=OrderResponse,
    status_code=status.HTTP_200_OK,
)
def complete_order_endpoint(
    order_id: int = Path(..., gt=0),
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    operator: OperatorORM = Depends(get_current_operator_dependency),
    db: Session = Depends(get_db),
):
    command = CompleteOrderCommand(
        operator_id=operator.id,
        order_id=order_id,
        idempotency_key=idempotency_key,
        completed_by=operator.email,
        source="API",
        notify_email=True,
        notify_push=True,
        note="Zamówienie zakończone przez operatora.",
    )

    try:
        return handle_complete_order(
            db=db,
            command=command,
        )

    except CartNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    except CartValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
