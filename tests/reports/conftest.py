from datetime import date

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from idp.email_and_password.repo import hash_password
from models import (
    CareVisit,
    Customer,
    Employee,
    EmployeeCareVisit,
    Schedule,
    ScheduleCustomer,
    ScheduleEmployee,
    User,
)


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
async def customer2(db: AsyncSession) -> Customer:
    c = Customer(
        first_name="Sven",
        last_name="Eriksson",
        key_number=1002,
        address="Lillgatan 5",
    )
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return c


@pytest_asyncio.fixture
async def schedule(db: AsyncSession) -> Schedule:
    s = Schedule(date=date(2026, 4, 1), shift_type="morning")
    db.add(s)
    await db.commit()
    await db.refresh(s)
    return s


@pytest_asyncio.fixture
async def populated_schedule(
    db: AsyncSession,
    schedule: Schedule,
    employee: Employee,
    employee2: Employee,
    customer: Customer,
    customer2: Customer,
) -> Schedule:
    """Schedule with 2 employees and 2 customers assigned, plus care visits."""
    # Assign employees and customers to schedule
    db.add(ScheduleEmployee(schedule_id=schedule.id, employee_id=employee.id))
    db.add(ScheduleEmployee(schedule_id=schedule.id, employee_id=employee2.id))
    db.add(ScheduleCustomer(schedule_id=schedule.id, customer_id=customer.id))
    db.add(ScheduleCustomer(schedule_id=schedule.id, customer_id=customer2.id))
    await db.commit()

    # Visit 1: employee visits customer, completed, 30 min
    v1 = CareVisit(
        date=schedule.date,
        schedule_id=schedule.id,
        customer_id=customer.id,
        duration=30,
        status="completed",
    )
    db.add(v1)
    await db.flush()
    db.add(
        EmployeeCareVisit(care_visit_id=v1.id, employee_id=employee.id, is_primary=True)
    )

    # Visit 2: employee visits customer2, completed, 45 min
    v2 = CareVisit(
        date=schedule.date,
        schedule_id=schedule.id,
        customer_id=customer2.id,
        duration=45,
        status="completed",
    )
    db.add(v2)
    await db.flush()
    db.add(
        EmployeeCareVisit(care_visit_id=v2.id, employee_id=employee.id, is_primary=True)
    )

    # Visit 3: employee2 visits customer, completed, 20 min
    v3 = CareVisit(
        date=schedule.date,
        schedule_id=schedule.id,
        customer_id=customer.id,
        duration=20,
        status="completed",
    )
    db.add(v3)
    await db.flush()
    db.add(
        EmployeeCareVisit(care_visit_id=v3.id, employee_id=employee2.id, is_primary=True)
    )

    # Visit 4: employee visits customer, canceled, 30 min (should not count)
    v4 = CareVisit(
        date=schedule.date,
        schedule_id=schedule.id,
        customer_id=customer.id,
        duration=30,
        status="canceled",
    )
    db.add(v4)
    await db.flush()
    db.add(
        EmployeeCareVisit(care_visit_id=v4.id, employee_id=employee.id, is_primary=True)
    )

    # Visit 5: double bemanning — both employees visit customer2, completed, 60 min
    v5 = CareVisit(
        date=schedule.date,
        schedule_id=schedule.id,
        customer_id=customer2.id,
        duration=60,
        status="completed",
    )
    db.add(v5)
    await db.flush()
    db.add(
        EmployeeCareVisit(care_visit_id=v5.id, employee_id=employee.id, is_primary=True)
    )
    db.add(
        EmployeeCareVisit(
            care_visit_id=v5.id, employee_id=employee2.id, is_primary=False
        )
    )

    await db.commit()
    return schedule
