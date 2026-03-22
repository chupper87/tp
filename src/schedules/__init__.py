from fastapi import APIRouter

from schedules.admin_api import router as admin_router
from schedules.public_api import router as public_router

router = APIRouter(prefix="/schedules")
router.include_router(admin_router)
router.include_router(public_router)
