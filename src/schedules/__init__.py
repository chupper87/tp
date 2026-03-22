from fastapi import APIRouter

from schedules.admin_api import router as admin_router

router = APIRouter(prefix="/schedules")
router.include_router(admin_router)
