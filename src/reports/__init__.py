from fastapi import APIRouter

from reports.admin_api import router as admin_router

router = APIRouter(prefix="/reports")
router.include_router(admin_router)
