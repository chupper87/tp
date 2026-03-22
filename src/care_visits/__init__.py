from fastapi import APIRouter

from care_visits.admin_api import router as admin_router
from care_visits.public_api import router as public_router

router = APIRouter(prefix="/care-visits")
router.include_router(admin_router)
router.include_router(public_router)
