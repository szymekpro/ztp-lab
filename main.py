from fastapi import FastAPI
from app.REST.web.routes import router
from app.notifications.web.routes import router as notifications_router

from app.REST.product_docs_app import products_docs_app
from app.REST.student_docs_app import students_docs_app
from app.notifications.docs_app import notifications_docs_app

app = FastAPI(title="Laboratorium 4 - Cały projekt")

app.include_router(router)
app.include_router(notifications_router, prefix="/api/v1")

app.mount("/students-docs", students_docs_app)
app.mount("/products-docs", products_docs_app)
app.mount("/notifications-docs", notifications_docs_app)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
