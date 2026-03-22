import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models import (
    CareVisit,
    Customer,
    Employee,
    EmployeeCareVisit,
    Schedule,
    ScheduleCustomer,
    ScheduleEmployee,
)


# --- auth / permissions ---


@pytest.mark.asyncio
async def test_employee_hours_requires_auth(client: AsyncClient) -> None:
    response = await client.get(
        "/reports/employee-hours?date_from=2026-04-01&date_to=2026-04-30"
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_employee_hours_requires_admin(
    authenticated_client: AsyncClient,
) -> None:
    response = await authenticated_client.get(
        "/reports/employee-hours?date_from=2026-04-01&date_to=2026-04-30"
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_customer_hours_requires_auth(client: AsyncClient) -> None:
    response = await client.get(
        "/reports/customer-hours?date_from=2026-04-01&date_to=2026-04-30"
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_visit_summary_requires_auth(client: AsyncClient) -> None:
    response = await client.get(
        "/reports/visit-summary?date_from=2026-04-01&date_to=2026-04-30"
    )
    assert response.status_code == 401


# --- empty reports ---


@pytest.mark.asyncio
async def test_employee_hours_empty(admin_client: AsyncClient) -> None:
    response = await admin_client.get(
        "/reports/employee-hours?date_from=2026-04-01&date_to=2026-04-30"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["date_from"] == "2026-04-01"
    assert data["date_to"] == "2026-04-30"
    assert data["rows"] == []


@pytest.mark.asyncio
async def test_customer_hours_empty(admin_client: AsyncClient) -> None:
    response = await admin_client.get(
        "/reports/customer-hours?date_from=2026-04-01&date_to=2026-04-30"
    )
    assert response.status_code == 200
    assert response.json()["rows"] == []


@pytest.mark.asyncio
async def test_visit_summary_empty(admin_client: AsyncClient) -> None:
    response = await admin_client.get(
        "/reports/visit-summary?date_from=2026-04-01&date_to=2026-04-30"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["by_status"] == []


# --- employee hours ---


@pytest.mark.asyncio
async def test_employee_hours_with_data(
    admin_client: AsyncClient,
    populated_schedule: Schedule,
    employee: Employee,
    employee2: Employee,
) -> None:
    """
    Completed visits:
    - employee:  30 + 45 + 60 = 135 min (3 visits)
    - employee2: 20 + 60 = 80 min (2 visits, one is double bemanning)
    The canceled visit (30 min) should NOT be counted.
    """
    response = await admin_client.get(
        "/reports/employee-hours?date_from=2026-04-01&date_to=2026-04-30"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["rows"]) == 2

    # Sorted by total_minutes desc, so employee first
    row1 = data["rows"][0]
    assert row1["employee_id"] == str(employee.id)
    assert row1["total_minutes"] == 135
    assert row1["visit_count"] == 3

    row2 = data["rows"][1]
    assert row2["employee_id"] == str(employee2.id)
    assert row2["total_minutes"] == 80
    assert row2["visit_count"] == 2


@pytest.mark.asyncio
async def test_employee_hours_date_filter(
    admin_client: AsyncClient,
    populated_schedule: Schedule,
) -> None:
    """All visits are on 2026-04-01. A date range that excludes it returns empty."""
    response = await admin_client.get(
        "/reports/employee-hours?date_from=2026-05-01&date_to=2026-05-31"
    )
    assert response.status_code == 200
    assert response.json()["rows"] == []


# --- customer hours ---


@pytest.mark.asyncio
async def test_customer_hours_with_data(
    admin_client: AsyncClient,
    populated_schedule: Schedule,
    customer: Customer,
    customer2: Customer,
) -> None:
    """
    Completed visits:
    - customer:  30 + 20 = 50 min (2 visits)
    - customer2: 45 + 60 = 105 min (2 visits)
    """
    response = await admin_client.get(
        "/reports/customer-hours?date_from=2026-04-01&date_to=2026-04-30"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["rows"]) == 2

    # Sorted by total_minutes desc, so customer2 first
    row1 = data["rows"][0]
    assert row1["customer_id"] == str(customer2.id)
    assert row1["total_minutes"] == 105
    assert row1["visit_count"] == 2

    row2 = data["rows"][1]
    assert row2["customer_id"] == str(customer.id)
    assert row2["total_minutes"] == 50
    assert row2["visit_count"] == 2


# --- visit summary ---


@pytest.mark.asyncio
async def test_visit_summary_with_data(
    admin_client: AsyncClient,
    populated_schedule: Schedule,
) -> None:
    """
    5 visits total: 4 completed, 1 canceled.
    """
    response = await admin_client.get(
        "/reports/visit-summary?date_from=2026-04-01&date_to=2026-04-30"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5

    status_map = {s["status"]: s["count"] for s in data["by_status"]}
    assert status_map["completed"] == 4
    assert status_map["canceled"] == 1


@pytest.mark.asyncio
async def test_visit_summary_date_filter(
    admin_client: AsyncClient,
    populated_schedule: Schedule,
) -> None:
    response = await admin_client.get(
        "/reports/visit-summary?date_from=2026-05-01&date_to=2026-05-31"
    )
    assert response.status_code == 200
    assert response.json()["total"] == 0


# --- required query params ---


@pytest.mark.asyncio
async def test_employee_hours_requires_dates(admin_client: AsyncClient) -> None:
    response = await admin_client.get("/reports/employee-hours")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_customer_hours_requires_dates(admin_client: AsyncClient) -> None:
    response = await admin_client.get("/reports/customer-hours")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_visit_summary_requires_dates(admin_client: AsyncClient) -> None:
    response = await admin_client.get("/reports/visit-summary")
    assert response.status_code == 422


# --- continuity ---


@pytest.mark.asyncio
async def test_continuity_requires_auth(client: AsyncClient) -> None:
    response = await client.get(
        "/reports/continuity?date_from=2026-04-01&date_to=2026-04-30"
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_continuity_requires_admin(
    authenticated_client: AsyncClient,
) -> None:
    response = await authenticated_client.get(
        "/reports/continuity?date_from=2026-04-01&date_to=2026-04-30"
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_continuity_empty(admin_client: AsyncClient) -> None:
    response = await admin_client.get(
        "/reports/continuity?date_from=2026-04-01&date_to=2026-04-30"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["rows"] == []
    assert data["average_score"] == 0.0


@pytest.mark.asyncio
async def test_continuity_requires_dates(admin_client: AsyncClient) -> None:
    response = await admin_client.get("/reports/continuity")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_continuity_with_data(
    admin_client: AsyncClient,
    populated_schedule: Schedule,
    customer: Customer,
    customer2: Customer,
) -> None:
    """
    From populated_schedule:
    - Birgitta: 2 completed visits by 2 unique employees → score 0.0
    - Sven: 2 completed visits by 2 unique employees → score 0.0
    """
    response = await admin_client.get(
        "/reports/continuity?date_from=2026-04-01&date_to=2026-04-30"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["rows"]) == 2
    assert data["average_score"] == 0.0

    by_customer = {r["customer_id"]: r for r in data["rows"]}
    birgitta = by_customer[str(customer.id)]
    assert birgitta["total_visits"] == 2
    assert birgitta["unique_employees"] == 2
    assert birgitta["continuity_score"] == 0.0

    sven = by_customer[str(customer2.id)]
    assert sven["total_visits"] == 2
    assert sven["unique_employees"] == 2
    assert sven["continuity_score"] == 0.0


@pytest.mark.asyncio
async def test_continuity_perfect_score(
    admin_client: AsyncClient,
    db: AsyncSession,
    employee: Employee,
    customer: Customer,
    schedule: Schedule,
) -> None:
    """All visits by the same employee = perfect continuity (1.0)."""
    db.add(ScheduleEmployee(schedule_id=schedule.id, employee_id=employee.id))
    db.add(ScheduleCustomer(schedule_id=schedule.id, customer_id=customer.id))
    await db.commit()

    for _ in range(3):
        v = CareVisit(
            date=schedule.date,
            schedule_id=schedule.id,
            customer_id=customer.id,
            duration=30,
            status="completed",
        )
        db.add(v)
        await db.flush()
        db.add(
            EmployeeCareVisit(
                care_visit_id=v.id, employee_id=employee.id, is_primary=True
            )
        )
    await db.commit()

    response = await admin_client.get(
        "/reports/continuity?date_from=2026-04-01&date_to=2026-04-30"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["rows"]) == 1
    assert data["rows"][0]["total_visits"] == 3
    assert data["rows"][0]["unique_employees"] == 1
    assert data["rows"][0]["continuity_score"] == 1.0
    assert data["average_score"] == 1.0


@pytest.mark.asyncio
async def test_continuity_single_visit(
    admin_client: AsyncClient,
    db: AsyncSession,
    employee: Employee,
    customer: Customer,
    schedule: Schedule,
) -> None:
    """A single visit should yield continuity 1.0."""
    db.add(ScheduleEmployee(schedule_id=schedule.id, employee_id=employee.id))
    db.add(ScheduleCustomer(schedule_id=schedule.id, customer_id=customer.id))
    await db.commit()

    v = CareVisit(
        date=schedule.date,
        schedule_id=schedule.id,
        customer_id=customer.id,
        duration=30,
        status="completed",
    )
    db.add(v)
    await db.flush()
    db.add(
        EmployeeCareVisit(care_visit_id=v.id, employee_id=employee.id, is_primary=True)
    )
    await db.commit()

    response = await admin_client.get(
        "/reports/continuity?date_from=2026-04-01&date_to=2026-04-30"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["rows"][0]["continuity_score"] == 1.0


@pytest.mark.asyncio
async def test_continuity_date_filter(
    admin_client: AsyncClient,
    populated_schedule: Schedule,
) -> None:
    """All visits are on 2026-04-01. Querying May returns empty."""
    response = await admin_client.get(
        "/reports/continuity?date_from=2026-05-01&date_to=2026-05-31"
    )
    assert response.status_code == 200
    assert response.json()["rows"] == []


# --- flex hours ---


@pytest.mark.asyncio
async def test_flex_hours_requires_auth(client: AsyncClient) -> None:
    response = await client.get(
        "/reports/flex-hours?date_from=2026-04-01&date_to=2026-04-30"
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_flex_hours_requires_admin(
    authenticated_client: AsyncClient,
) -> None:
    response = await authenticated_client.get(
        "/reports/flex-hours?date_from=2026-04-01&date_to=2026-04-30"
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_flex_hours_empty(admin_client: AsyncClient) -> None:
    response = await admin_client.get(
        "/reports/flex-hours?date_from=2026-04-01&date_to=2026-04-30"
    )
    assert response.status_code == 200
    assert response.json()["rows"] == []


@pytest.mark.asyncio
async def test_flex_hours_requires_dates(admin_client: AsyncClient) -> None:
    response = await admin_client.get("/reports/flex-hours")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_flex_hours_with_data(
    admin_client: AsyncClient,
    populated_schedule: Schedule,
    employee: Employee,
    employee2: Employee,
) -> None:
    """
    Completed visits (from populated_schedule):
    - Pelle: 30 + 45 + 60 = 135 min worked
    - Anna: 20 + 60 = 80 min worked
    Period: 2026-04-01 to 2026-04-30 = 30 days
    """
    response = await admin_client.get(
        "/reports/flex-hours?date_from=2026-04-01&date_to=2026-04-30"
    )
    assert response.status_code == 200
    data = response.json()

    by_emp = {r["employee_id"]: r for r in data["rows"]}
    assert by_emp[str(employee.id)]["worked_minutes"] == 135
    assert by_emp[str(employee2.id)]["worked_minutes"] == 80


@pytest.mark.asyncio
async def test_flex_hours_with_weekly_hours(
    admin_client: AsyncClient,
    db: AsyncSession,
    employee: Employee,
    schedule: Schedule,
) -> None:
    """Employee with weekly_hours set should show contracted and flex."""
    employee.weekly_hours = 40.0
    db.add(employee)
    await db.commit()

    db.add(ScheduleEmployee(schedule_id=schedule.id, employee_id=employee.id))
    await db.commit()

    v = CareVisit(
        date=schedule.date,
        schedule_id=schedule.id,
        customer_id=None,  # will set below
        duration=480,
        status="completed",
    )
    # Need a customer on the schedule for a valid visit
    from models import Customer

    cust = Customer(first_name="Test", last_name="Kund", key_number=9999, address="X")
    db.add(cust)
    await db.commit()
    await db.refresh(cust)
    db.add(ScheduleCustomer(schedule_id=schedule.id, customer_id=cust.id))
    await db.commit()

    v = CareVisit(
        date=schedule.date,
        schedule_id=schedule.id,
        customer_id=cust.id,
        duration=480,
        status="completed",
    )
    db.add(v)
    await db.flush()
    db.add(
        EmployeeCareVisit(care_visit_id=v.id, employee_id=employee.id, is_primary=True)
    )
    await db.commit()

    # Query for exactly 1 week so contracted = 40 * 60 = 2400 min
    response = await admin_client.get(
        "/reports/flex-hours?date_from=2026-03-30&date_to=2026-04-05"
    )
    assert response.status_code == 200
    data = response.json()

    by_emp = {r["employee_id"]: r for r in data["rows"]}
    row = by_emp[str(employee.id)]
    assert row["worked_minutes"] == 480
    assert row["contracted_minutes"] == 2400  # 40h * 60min * 7days/7
    assert row["flex_minutes"] == 480 - 2400  # -1920


@pytest.mark.asyncio
async def test_flex_hours_null_weekly_hours(
    admin_client: AsyncClient,
    db: AsyncSession,
    employee: Employee,
) -> None:
    """Employee without weekly_hours has null contracted and flex."""
    employee.weekly_hours = None
    db.add(employee)
    await db.commit()

    response = await admin_client.get(
        "/reports/flex-hours?date_from=2026-04-01&date_to=2026-04-30"
    )
    assert response.status_code == 200
    data = response.json()

    by_emp = {r["employee_id"]: r for r in data["rows"]}
    row = by_emp[str(employee.id)]
    assert row["worked_minutes"] == 0
    assert row["contracted_minutes"] is None
    assert row["flex_minutes"] is None
