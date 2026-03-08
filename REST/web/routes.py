from fastapi import APIRouter

from web.student_routes import router as student_router
from web.product_routes import router as product_router

router = APIRouter(prefix="/api/v1")

router.include_router(student_router)
router.include_router(product_router)
