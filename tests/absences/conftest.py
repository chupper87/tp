import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from idp.core import AUTH_COOKIE_NAME, AuthenticationJWT
from idp.email_and_password.repo import hash_password
from models import Employee, User


@pytest_asyncio.fixture
async def employee(db: AsyncSession) -> Employee:
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
    await db.refresh(e)
    return e


@pytest_asyncio.fixture
async def employee2(db: AsyncSession) -> Employee:
    u = User(
        email="worker2@test.com",
        hashed_password=hash_password("pw"),
        is_active=True,
        is_admin=False,
    )
    db.add(u)
    await db.commit()
    await db.refresh(u)

    e = Employee(first_name="Anna", last_name="Johansson", user_id=u.id)
    db.add(e)
    await db.commit()
    await db.refresh(e)
    return e


@pytest_asyncio.fixture
async def employee_client(client: AsyncClient, employee: Employee):
    """Separate HTTP client authenticated as the employee's user.

    Uses its own AsyncClient so it doesn't share cookies with admin_client.
    Depends on ``client`` to ensure the DB override is active.
    """
    from httpx import ASGITransport

    from api import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        jwt = AuthenticationJWT.create(user_id=employee.user_id)
        ac.cookies.set(AUTH_COOKIE_NAME, jwt.token)
        yield ac
