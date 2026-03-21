from fastapi import APIRouter

from measures.admin_api import router as admin_router

router = APIRouter(prefix="/measures")
router.include_router(admin_router)
