import pytest
from httpx import AsyncClient

from models import Employee


# --- auth ---


@pytest.mark.asyncio
async def test_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/absences/my/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_requires_employee_profile(authenticated_client: AsyncClient) -> None:
    response = await authenticated_client.get("/absences/my/")
    assert response.status_code == 403


# --- list my absences ---


@pytest.mark.asyncio
async def test_list_empty(employee_client: AsyncClient) -> None:
    response = await employee_client.get("/absences/my/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_my_absences(
    employee_client: AsyncClient,
    admin_client: AsyncClient,
    employee: Employee,
) -> None:
    """Employee sees their own absences."""
    resp = await admin_client.post(
        "/absences/",
        json={
            "employee_id": str(employee.id),
            "absence_type": "sick",
            "start_date": "2026-04-01",
            "end_date": "2026-04-03",
        },
    )
    assert resp.status_code == 201
    absence_id = resp.json()["id"]

    response = await employee_client.get("/absences/my/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == absence_id


@pytest.mark.asyncio
async def test_does_not_show_other_employees_absences(
    employee_client: AsyncClient,
    admin_client: AsyncClient,
    employee2: Employee,
) -> None:
    """Employee should not see absences belonging to another employee."""
    resp = await admin_client.post(
        "/absences/",
        json={
            "employee_id": str(employee2.id),
            "absence_type": "vacation",
            "start_date": "2026-05-01",
            "end_date": "2026-05-05",
        },
    )
    assert resp.status_code == 201

    response = await employee_client.get("/absences/my/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_filter_by_type(
    employee_client: AsyncClient,
    admin_client: AsyncClient,
    employee: Employee,
) -> None:
    await admin_client.post(
        "/absences/",
        json={
            "employee_id": str(employee.id),
            "absence_type": "sick",
            "start_date": "2026-04-01",
            "end_date": "2026-04-03",
        },
    )
    await admin_client.post(
        "/absences/",
        json={
            "employee_id": str(employee.id),
            "absence_type": "vacation",
            "start_date": "2026-05-01",
            "end_date": "2026-05-05",
        },
    )

    response = await employee_client.get("/absences/my/?absence_type=vacation")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["absence_type"] == "vacation"


@pytest.mark.asyncio
async def test_filter_by_date_range(
    employee_client: AsyncClient,
    admin_client: AsyncClient,
    employee: Employee,
) -> None:
    await admin_client.post(
        "/absences/",
        json={
            "employee_id": str(employee.id),
            "absence_type": "sick",
            "start_date": "2026-04-01",
            "end_date": "2026-04-03",
        },
    )

    response = await employee_client.get(
        "/absences/my/?date_from=2026-05-01&date_to=2026-05-31"
    )
    assert response.status_code == 200
    assert response.json() == []

    response = await employee_client.get(
        "/absences/my/?date_from=2026-04-01&date_to=2026-04-30"
    )
    assert response.status_code == 200
    assert len(response.json()) == 1
