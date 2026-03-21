from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from idp.core import AUTH_COOKIE_NAME, AuthenticationJWT, get_authenticated_user
from idp.email_and_password import repo
from log_setup import get_logger
from models import User

log = get_logger(__name__)

router = APIRouter(tags=["Auth"])


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: UUID
    email: str
    is_admin: bool
    is_active: bool


def _user_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        email=user.email,
        is_admin=user.is_admin,
        is_active=user.is_active,
    )


class LoginOut(BaseModel):
    user: UserOut


@router.post("/login", response_model=LoginOut)
async def login(
    body: LoginIn,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    try:
        user = await repo.authenticate_user(db, email=body.email, password=body.password)
    except (repo.InvalidCredentials, repo.InactiveUser):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = AuthenticationJWT.create(user_id=user.id)
    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=token.token,
        expires=token.expiration,
        httponly=True,
        samesite="lax",
    )

    log.info("User logged in", user_id=str(user.id), email=user.email)
    return LoginOut(user=_user_out(user))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response):
    response.delete_cookie(key=AUTH_COOKIE_NAME)


@router.get("/me", response_model=UserOut)
async def get_me(user: User = Depends(get_authenticated_user)) -> UserOut:
    return _user_out(user)
