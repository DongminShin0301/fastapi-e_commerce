from fastapi import APIRouter
from app.api.v1.endpoints.users import router as users_router
from app.api.v1.endpoints.products import router as products_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.cart import router as cart_router
from app.api.v1.endpoints.order import router as order_router

router = APIRouter()

router.include_router(users_router)
router.include_router(products_router)
router.include_router(auth_router)
router.include_router(cart_router)
router.include_router(order_router)
