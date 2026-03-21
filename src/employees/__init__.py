from fastapi import APIRouter

from employees.admin_api import router as admin_router

router = APIRouter(prefix="/employees")
router.include_router(admin_router)
