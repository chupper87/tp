from fastapi import APIRouter

from care_visits.admin_api import router as admin_router

router = APIRouter(prefix="/care-visits")
router.include_router(admin_router)
