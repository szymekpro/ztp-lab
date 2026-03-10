from pydantic import BaseModel


class Category(BaseModel):
    id: int
    name: str
    min_price: float
    max_price: float

    class Config:
        from_attributes = True


class Product(BaseModel):
    id: int
    name: str
    category: Category
    price: float
    quantity: int

    class Config:
        from_attributes = True


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
