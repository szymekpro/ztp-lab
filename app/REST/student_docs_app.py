from fastapi import FastAPI

from app.REST.web.student_routes import router as student_router


students_docs_app = FastAPI(
    title="Students API",
    docs_url="/",
    redoc_url=None,
    openapi_url="/openapi.json",
)

students_docs_app.include_router(student_router, prefix="/api/v1", tags=["students"])
