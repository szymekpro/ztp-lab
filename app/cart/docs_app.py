from fastapi import FastAPI
from app.cart.web.routes import router as cart_router
from app.cart.web.routes import orders_router

cart_docs_app = FastAPI(
    title="Cart API",
    docs_url="/",
    redoc_url=None,
    openapi_url="/openapi.json",
)

cart_docs_app.include_router(cart_router)
cart_docs_app.include_router(orders_router)
