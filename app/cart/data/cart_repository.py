from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.cart.model.cart_draft_item_orm import CartDraftItemORM
from app.cart.model.cart_draft_orm import CartDraftORM
from app.cart.model.order_item_orm import OrderItemORM
from app.cart.model.order_orm import OrderORM
from app.cart.model.processed_command_orm import ProcessedCommandORM


def get_cart_by_operator_id(
    db: Session,
    operator_id: int,
) -> CartDraftORM | None:
    query = (
        select(CartDraftORM)
        .where(CartDraftORM.operator_id == operator_id)
        .options(
            selectinload(CartDraftORM.items)
            .selectinload(CartDraftItemORM.product)
        )
    )
    result = db.execute(query)
    return result.scalars().first()


def create_cart(
    db: Session,
    operator_id: int,
) -> CartDraftORM:
    cart = CartDraftORM(operator_id=operator_id)
    db.add(cart)
    db.commit()
    db.refresh(cart)
    return cart


def get_or_create_cart(
    db: Session,
    operator_id: int,
) -> CartDraftORM:
    cart = get_cart_by_operator_id(db, operator_id)

    if cart is not None:
        return cart

    return create_cart(db, operator_id)


def get_cart_item_by_cart_and_product(
    db: Session,
    cart_id: int,
    product_id: int,
) -> CartDraftItemORM | None:
    query = select(CartDraftItemORM).where(
        CartDraftItemORM.cart_id == cart_id,
        CartDraftItemORM.product_id == product_id,
    )
    result = db.execute(query)
    return result.scalars().first()


def get_cart_item_by_id(
    db: Session,
    item_id: int,
) -> CartDraftItemORM | None:
    query = (
        select(CartDraftItemORM)
        .where(CartDraftItemORM.id == item_id)
        .options(selectinload(CartDraftItemORM.product))
    )
    result = db.execute(query)
    return result.scalars().first()


def add_cart_item(
    db: Session,
    cart_id: int,
    product_id: int,
    quantity: int,
) -> CartDraftItemORM:
    item = CartDraftItemORM(
        cart_id=cart_id,
        product_id=product_id,
        quantity=quantity,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_cart_item_quantity(
    db: Session,
    item: CartDraftItemORM,
    quantity: int,
) -> CartDraftItemORM:
    item.quantity = quantity
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def delete_cart_item(
    db: Session,
    item: CartDraftItemORM,
) -> None:
    db.delete(item)
    db.commit()


def clear_cart_items(
    db: Session,
    cart_id: int,
) -> None:
    query = delete(CartDraftItemORM).where(CartDraftItemORM.cart_id == cart_id)
    db.execute(query)
    db.commit()


def add_order(
    db: Session,
    order: OrderORM,
) -> OrderORM:
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def add_order_item(
    db: Session,
    item: OrderItemORM,
) -> OrderItemORM:
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def get_orders_by_operator_id(
    db: Session,
    operator_id: int,
) -> list[OrderORM]:
    query = (
        select(OrderORM)
        .where(OrderORM.operator_id == operator_id)
        .order_by(OrderORM.created_at.desc())
    )
    result = db.execute(query)
    return list(result.scalars().all())


def get_order_by_id_and_operator_id(
    db: Session,
    order_id: int,
    operator_id: int,
) -> OrderORM | None:
    query = (
        select(OrderORM)
        .where(
            OrderORM.id == order_id,
            OrderORM.operator_id == operator_id,
        )
        .options(selectinload(OrderORM.items))
    )
    result = db.execute(query)
    return result.scalars().first()


def save_order(
    db: Session,
    order: OrderORM,
) -> OrderORM:
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def get_processed_command(
    db: Session,
    command_name: str,
    idempotency_key: str,
) -> ProcessedCommandORM | None:
    query = select(ProcessedCommandORM).where(
        ProcessedCommandORM.command_name == command_name,
        ProcessedCommandORM.idempotency_key == idempotency_key,
    )
    result = db.execute(query)
    return result.scalars().first()


def add_processed_command(
    db: Session,
    command_name: str,
    idempotency_key: str,
    operator_id: int,
) -> ProcessedCommandORM:
    processed_command = ProcessedCommandORM(
        command_name=command_name,
        idempotency_key=idempotency_key,
        operator_id=operator_id,
    )
    db.add(processed_command)
    db.commit()
    db.refresh(processed_command)
    return processed_command


def is_command_already_processed(
    db: Session,
    command_name: str,
    idempotency_key: str,
) -> bool:
    return get_processed_command(
        db=db,
        command_name=command_name,
        idempotency_key=idempotency_key,
    ) is not None
