from fastapi import APIRouter

from absences.admin_api import router as admin_router
from absences.public_api import router as public_router

router = APIRouter(prefix="/absences")
router.include_router(admin_router)
router.include_router(public_router)
