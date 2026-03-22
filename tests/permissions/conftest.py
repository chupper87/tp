import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from idp.core import AUTH_COOKIE_NAME, AuthenticationJWT
from idp.email_and_password.repo import hash_password
from models import Employee, User


@pytest_asyncio.fixture
async def employee_user(db: AsyncSession) -> User:
    """A regular user with a linked employee profile."""
    u = User(
        email="worker@test.com",
        hashed_password=hash_password("pw"),
        is_active=True,
        is_admin=False,
    )
    db.add(u)
    await db.commit()
    await db.refresh(u)

    e = Employee(first_name="Pelle", last_name="Svensson", user_id=u.id)
    db.add(e)
    await db.commit()
    return u


@pytest_asyncio.fixture
async def employee_client(client: AsyncClient, employee_user: User):
    """Separate HTTP client authenticated as the employee user."""
    from httpx import ASGITransport

    from api import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        jwt = AuthenticationJWT.create(user_id=employee_user.id)
        ac.cookies.set(AUTH_COOKIE_NAME, jwt.token)
        yield ac
