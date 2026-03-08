from pydantic import BaseModel


class Product(BaseModel):
    id: int
    name: str
    category_id: int
    price: float

    class Config:
        from_attributes = True
