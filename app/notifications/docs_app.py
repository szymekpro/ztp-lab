from fastapi import FastAPI
from app.notifications.web.routes import router as notifications_router

notifications_docs_app = FastAPI(
    title="Notifications API",
    docs_url="/",
    redoc_url=None,
    openapi_url="/openapi.json"
)

notifications_docs_app.include_router(notifications_router, prefix="/api/v1")