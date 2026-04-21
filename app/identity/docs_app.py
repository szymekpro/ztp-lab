from fastapi import FastAPI

from app.identity.web.routes import router as identity_router

identity_docs_app = FastAPI(
    title="Identity API",
    docs_url="/",
    redoc_url=None,
    openapi_url="/openapi.json",
)

identity_docs_app.include_router(identity_router)