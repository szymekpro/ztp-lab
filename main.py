from contextlib import asynccontextmanager
from threading import Thread

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.notifications.service.notification_worker import run_worker

from app.REST.web.routes import router
from app.notifications.web.routes import router as notifications_router
from app.identity.web.routes import router as identity_router


from app.REST.product_docs_app import products_docs_app
from app.notifications.docs_app import notifications_docs_app
from app.identity.docs_app import identity_docs_app
from app.cart.docs_app import cart_docs_app
from app.cart.web.routes import router as cart_router
from app.cart.web.routes import orders_router as cart_orders_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    thread = Thread(target=run_worker, daemon=True)
    thread.start()
    yield


app = FastAPI(
    title="Laboratorium 10 - React Frontend",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(notifications_router, prefix="/api/v1")
app.include_router(identity_router, prefix="/api/v1")
app.include_router(cart_router, prefix="/api/v1")
app.include_router(cart_orders_router, prefix="/api/v1")

app.mount("/products-docs", products_docs_app)
app.mount("/notifications-docs", notifications_docs_app)
app.mount("/identity-docs", identity_docs_app)
app.mount("/cart-docs", cart_docs_app)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
