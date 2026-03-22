from datetime import date

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from idp.core import AUTH_COOKIE_NAME, AuthenticationJWT
from idp.email_and_password.repo import hash_password
from models import Customer, Employee, Measure, Schedule, ScheduleEmployee, User


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
async def customer(db: AsyncSession) -> Customer:
    c = Customer(
        first_name="Birgitta",
        last_name="Karlsson",
        key_number=1001,
        address="Storgatan 1",
    )
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return c


@pytest_asyncio.fixture
async def measure(db: AsyncSession) -> Measure:
    m = Measure(name="Shower", default_duration=30, is_standard=True)
    db.add(m)
    await db.commit()
    await db.refresh(m)
    return m


@pytest_asyncio.fixture
async def schedule(db: AsyncSession) -> Schedule:
    s = Schedule(date=date(2026, 4, 1), shift_type="morning")
    db.add(s)
    await db.commit()
    await db.refresh(s)
    return s


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


@pytest_asyncio.fixture
async def schedule_with_employee(
    db: AsyncSession, schedule: Schedule, employee: Employee
) -> Schedule:
    """Schedule with one employee assigned."""
    db.add(ScheduleEmployee(schedule_id=schedule.id, employee_id=employee.id))
    await db.commit()
    return schedule
