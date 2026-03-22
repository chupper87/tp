from fastapi import APIRouter

from absences.admin_api import router as admin_router

router = APIRouter(prefix="/absences")
router.include_router(admin_router)
