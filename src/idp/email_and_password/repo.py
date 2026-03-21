import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from log_setup import get_logger
from models import User

log = get_logger(__name__)


class InvalidCredentials(Exception):
    pass


class InactiveUser(Exception):
    pass


def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(plain_password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email.lower()))
    return result.scalar_one_or_none()


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
    """
    Raises:
        InvalidCredentials: if email not found or password is wrong
        InactiveUser: if the user account is inactive
    """
    user = await get_user_by_email(db, email)

    if user is None or not verify_password(password, user.hashed_password):
        log.info("Failed login attempt", email=email)
        raise InvalidCredentials("Invalid email or password")

    if not user.is_active:
        log.info("Login attempt for inactive user", email=email)
        raise InactiveUser("User account is inactive")

    return user
