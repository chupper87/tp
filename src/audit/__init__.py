from fastapi import APIRouter

from audit.admin_api import router as admin_router

router = APIRouter(prefix="/audit")
router.include_router(admin_router)
