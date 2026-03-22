from fastapi import APIRouter

from permissions.admin_api import router as admin_router

router = APIRouter(prefix="/permissions")
router.include_router(admin_router)
