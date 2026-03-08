from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from service.product_service import list_products, get_product
from data.database import get_db
from model.product_schema import Product

router = APIRouter()


@router.get("/products", response_model=list[Product])
def get_products(db: Session = Depends(get_db)):
    return list_products(db)


@router.get("/products/{id}", response_model=Product)
def get_product_by_id(id: int, db: Session = Depends(get_db)):
    product = get_product(db, id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product
