from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyCookie
from jose import ExpiredSignatureError, JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from structlog.contextvars import bind_contextvars

from config import config
from database import get_db
from log_setup import get_logger
from models import User

log = get_logger(__name__)

AUTH_COOKIE_NAME = "tp-token"

_cookie_scheme = APIKeyCookie(name=AUTH_COOKIE_NAME, auto_error=False)


class TokenPayload(BaseModel):
    user_id: UUID


class AuthenticationJWT(BaseModel):
    token: str
    expiration: datetime

    @classmethod
    def create(cls, user_id: UUID) -> "AuthenticationJWT":
        expiration = datetime.now(tz=timezone.utc) + timedelta(
            hours=config.JWT_EXPIRATION_TIME_IN_HOURS
        )
        payload = TokenPayload(user_id=user_id)
        token: str = jwt.encode(
            claims={
                "pld": payload.model_dump(mode="json"),
                "exp": expiration,
                "sub": str(user_id),
            },
            key=config.SECRET_JWT_SIGNING_KEY.get_secret_value(),
            algorithm="HS256",
        )
        return cls(token=token, expiration=expiration)


class ValidTokenButUserDoesNotExist(Exception):
    pass


class InvalidTokenClaims(Exception):
    pass


async def _get_user_from_token(db: AsyncSession, token: str) -> User:
    try:
        claims = jwt.decode(
            token,
            key=config.SECRET_JWT_SIGNING_KEY.get_secret_value(),
            algorithms=["HS256"],
        )
    except Exception as e:
        log.debug("Failed to decode JWT", error=str(e))
        raise

    try:
        payload = TokenPayload(**claims["pld"])
    except Exception as e:
        log.warning("JWT payload claims were invalid", error=str(e))
        raise InvalidTokenClaims(f"Invalid JWT claims: {e}") from e

    user = await db.get(User, payload.user_id)
    if user is None:
        log.warning(
            "Valid token but user does not exist",
            user_id=str(payload.user_id),
        )
        raise ValidTokenButUserDoesNotExist("Valid token but no such user exists")

    return user


async def get_authenticated_user(
    cookie: Optional[str] = Security(_cookie_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if cookie is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    try:
        user = await _get_user_from_token(db, cookie)
    except Exception as e:
        match e:
            case ExpiredSignatureError():
                detail = "Session expired, please log in again"
            case ValidTokenButUserDoesNotExist():
                detail = "User no longer exists"
            case InvalidTokenClaims() | JWTError():
                detail = "Invalid authentication token"
            case _:
                detail = "Authentication failed"

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
        ) from e

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    log.debug("Authenticated user", user_id=str(user.id))
    bind_contextvars(authenticated_user_id=str(user.id))
    return user


async def get_authenticated_admin_user(
    user: User = Depends(get_authenticated_user),
) -> User:
    if not user.is_admin:
        log.debug("User is not admin, denying request", user_id=str(user.id))
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    bind_contextvars(authenticated_admin_user_id=str(user.id))
    return user
