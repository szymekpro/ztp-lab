from fastapi import APIRouter

from .product_routes import router as product_router

router = APIRouter(prefix="/api/v1")

router.include_router(product_router, prefix="/product", tags=["products"])
