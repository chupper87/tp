import pytest
from httpx import AsyncClient

from models import Schedule


# --- auth ---


@pytest.mark.asyncio
async def test_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/schedules/my/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_requires_employee_profile(authenticated_client: AsyncClient) -> None:
    """A user without a linked employee gets 403."""
    response = await authenticated_client.get("/schedules/my/")
    assert response.status_code == 403


# --- list my schedules ---


@pytest.mark.asyncio
async def test_list_empty(employee_client: AsyncClient) -> None:
    response = await employee_client.get("/schedules/my/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_assigned_schedules(
    employee_client: AsyncClient, schedule_with_employee: Schedule
) -> None:
    response = await employee_client.get("/schedules/my/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == str(schedule_with_employee.id)


@pytest.mark.asyncio
async def test_does_not_show_unassigned_schedules(
    employee_client: AsyncClient, schedule: Schedule
) -> None:
    """Employee not assigned to this schedule should not see it."""
    response = await employee_client.get("/schedules/my/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_filter_by_date_range(
    employee_client: AsyncClient,
    schedule_with_employee: Schedule,
) -> None:
    response = await employee_client.get(
        "/schedules/my/?date_from=2026-05-01&date_to=2026-05-31"
    )
    assert response.status_code == 200
    assert response.json() == []

    response = await employee_client.get(
        "/schedules/my/?date_from=2026-04-01&date_to=2026-04-30"
    )
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_filter_by_shift_type(
    employee_client: AsyncClient,
    schedule_with_employee: Schedule,
) -> None:
    response = await employee_client.get("/schedules/my/?shift_type=evening")
    assert response.status_code == 200
    assert response.json() == []

    response = await employee_client.get("/schedules/my/?shift_type=morning")
    assert response.status_code == 200
    assert len(response.json()) == 1
