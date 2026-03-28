from fastapi import FastAPI

from app.REST.web.product_routes import router as product_router


products_docs_app = FastAPI(
    title="Products API",
    docs_url="/",
    redoc_url=None,
    openapi_url="/openapi.json",
)

products_docs_app.include_router(product_router, prefix="/api/v1", tags=["products"])
