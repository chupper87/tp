import pytest
from httpx import AsyncClient

from models import Customer, Employee, Schedule


# --- auth ---


@pytest.mark.asyncio
async def test_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/care-visits/my/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_requires_employee_profile(authenticated_client: AsyncClient) -> None:
    response = await authenticated_client.get("/care-visits/my/")
    assert response.status_code == 403


# --- list my care visits ---


@pytest.mark.asyncio
async def test_list_empty(employee_client: AsyncClient) -> None:
    response = await employee_client.get("/care-visits/my/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_my_visits(
    employee_client: AsyncClient,
    admin_client: AsyncClient,
    schedule_with_employee_and_customer: Schedule,
    employee: Employee,
    customer: Customer,
) -> None:
    """Employee sees visits they are assigned to."""
    # Create a visit via admin
    resp = await admin_client.post(
        "/care-visits/",
        json={
            "schedule_id": str(schedule_with_employee_and_customer.id),
            "customer_id": str(customer.id),
            "duration": 30,
            "employees": [{"employee_id": str(employee.id), "is_primary": True}],
        },
    )
    assert resp.status_code == 201
    visit_id = resp.json()["id"]

    # Employee should see it
    response = await employee_client.get("/care-visits/my/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == visit_id


@pytest.mark.asyncio
async def test_does_not_show_other_employees_visits(
    employee_client: AsyncClient,
    admin_client: AsyncClient,
    schedule_with_two_employees_and_customer: Schedule,
    employee2: Employee,
    customer: Customer,
) -> None:
    """Employee should not see visits assigned only to another employee."""
    # Create a visit with only employee2
    resp = await admin_client.post(
        "/care-visits/",
        json={
            "schedule_id": str(schedule_with_two_employees_and_customer.id),
            "customer_id": str(customer.id),
            "duration": 30,
            "employees": [{"employee_id": str(employee2.id), "is_primary": True}],
        },
    )
    assert resp.status_code == 201

    # employee (not employee2) should not see it
    response = await employee_client.get("/care-visits/my/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_filter_by_status(
    employee_client: AsyncClient,
    admin_client: AsyncClient,
    schedule_with_employee_and_customer: Schedule,
    employee: Employee,
    customer: Customer,
) -> None:
    resp = await admin_client.post(
        "/care-visits/",
        json={
            "schedule_id": str(schedule_with_employee_and_customer.id),
            "customer_id": str(customer.id),
            "duration": 30,
            "employees": [{"employee_id": str(employee.id), "is_primary": True}],
        },
    )
    assert resp.status_code == 201

    response = await employee_client.get("/care-visits/my/?status_filter=completed")
    assert response.status_code == 200
    assert response.json() == []

    response = await employee_client.get("/care-visits/my/?status_filter=planned")
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_filter_by_date_range(
    employee_client: AsyncClient,
    admin_client: AsyncClient,
    schedule_with_employee_and_customer: Schedule,
    employee: Employee,
    customer: Customer,
) -> None:
    resp = await admin_client.post(
        "/care-visits/",
        json={
            "schedule_id": str(schedule_with_employee_and_customer.id),
            "customer_id": str(customer.id),
            "duration": 30,
            "employees": [{"employee_id": str(employee.id), "is_primary": True}],
        },
    )
    assert resp.status_code == 201

    response = await employee_client.get(
        "/care-visits/my/?date_from=2026-05-01&date_to=2026-05-31"
    )
    assert response.status_code == 200
    assert response.json() == []

    response = await employee_client.get(
        "/care-visits/my/?date_from=2026-04-01&date_to=2026-04-30"
    )
    assert response.status_code == 200
    assert len(response.json()) == 1
