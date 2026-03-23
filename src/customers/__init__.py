from fastapi import APIRouter

from customers.admin_api import router as admin_router
from customers.care_plan_api import router as care_plan_router

router = APIRouter(prefix="/customers")
router.include_router(admin_router)
router.include_router(care_plan_router)
