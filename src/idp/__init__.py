from fastapi import APIRouter

from idp.email_and_password.api import router as email_and_password_router

router = APIRouter(prefix="/auth")
router.include_router(email_and_password_router)
