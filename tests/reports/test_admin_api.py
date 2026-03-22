import pytest
from httpx import AsyncClient

from models import Customer, Employee, Schedule


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
