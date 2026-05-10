from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class CartItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)


class CartItemUpdate(BaseModel):
    quantity: int = Field(..., gt=0)


class CartProductResponse(BaseModel):
    id: int
    name: str
    price: float
    quantity: int

    model_config = ConfigDict(from_attributes=True)


class CartDraftItemResponse(BaseModel):
    id: int
    product: CartProductResponse
    quantity: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CartDraftResponse(BaseModel):
    id: int
    operator_id: int
    items: list[CartDraftItemResponse]
    items_count: int
    total_price: float
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    product_price: float
    quantity: int

    model_config = ConfigDict(from_attributes=True)


class OrderResponse(BaseModel):
    id: int
    operator_id: int
    order_number: str
    status: str
    items_count: int
    total_price: float
    created_at: datetime
    items: list[OrderItemResponse]

    model_config = ConfigDict(from_attributes=True)


class OrderListItemResponse(BaseModel):
    id: int
    order_number: str
    status: str
    items_count: int
    total_price: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
