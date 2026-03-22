from datetime import date

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from idp.email_and_password.repo import hash_password
from models import Customer, Employee, Measure, Schedule, User


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
