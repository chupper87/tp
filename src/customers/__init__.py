from fastapi import APIRouter

from customers.admin_api import router as admin_router

router = APIRouter(prefix="/customers")
router.include_router(admin_router)
