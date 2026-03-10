# web/product_routes.py
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from service.product_service import (
    create_product, list_products, get_product,
    replace_product, patch_product as patch_product_service, remove_product,
)
from service.product_validators import ValidationError, ConflictError, ResourceNotFoundError
from data.database import get_db
from model.product_schema import Product, ProductCreate, ProductUpdate

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


@router.post("/products", response_model=Product, status_code=201)
def post_product(payload: ProductCreate, db: Session = Depends(get_db)):
    try:
        return create_product(db, payload)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/products/{id}", response_model=Product)
def put_product(id: int, payload: ProductCreate, db: Session = Depends(get_db)):
    try:
        product = replace_product(db, id, payload)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.patch("/products/{id}", response_model=Product)
def patch_product_endpoint(id: int, payload: ProductUpdate, db: Session = Depends(get_db)):
    try:
        product = patch_product_service(db, id, payload)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.delete("/products/{id}", status_code=204)
def delete_product_endpoint(id: int, db: Session = Depends(get_db)):
    if not remove_product(db, id):
        raise HTTPException(status_code=404, detail="Product not found")

    return Response(status_code=204)
