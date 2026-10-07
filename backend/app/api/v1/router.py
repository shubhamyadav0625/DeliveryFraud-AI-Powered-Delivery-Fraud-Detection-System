from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.orders import router as orders_router
from app.api.v1.packing import router as packing_router
from app.api.v1.deliveries import router as deliveries_router
from app.api.v1.claims import router as claims_router
from app.api.v1.admin import router as admin_router
from app.api.v1.customers import router as customers_router

api_v1_router = APIRouter()
api_v1_router.include_router(auth_router)
api_v1_router.include_router(orders_router)
api_v1_router.include_router(packing_router)
api_v1_router.include_router(deliveries_router)
api_v1_router.include_router(claims_router)
api_v1_router.include_router(admin_router)
api_v1_router.include_router(customers_router)
