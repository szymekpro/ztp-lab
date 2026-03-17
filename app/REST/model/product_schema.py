import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class Category(BaseModel):
    id: int
    name: str
    min_price: float
    max_price: float

    model_config = ConfigDict(from_attributes=True)


class Product(BaseModel):
    id: int
    name: str
    category: Category
    price: float
    quantity: int

    model_config = ConfigDict(from_attributes=True)


class ProductCreate(BaseModel):
    name: str
    category_id: int
    price: float
    quantity: int


class ProductUpdate(BaseModel):
    name: str | None = None
    category_id: int | None = None
    price: float | None = None
    quantity: int | None = None


class ProductHistoryEntry(BaseModel):
    id: int
    product_id: int
    action: str
    previous_state: dict[str, Any]
    current_state: dict[str, Any]
    changed_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)
