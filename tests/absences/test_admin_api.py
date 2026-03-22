import uuid

import pytest
from httpx import AsyncClient

from models import Employee


def _absence_payload(employee: Employee, **overrides) -> dict:
    return {
        "employee_id": str(employee.id),
        "absence_type": "sick",
        "start_date": "2026-04-01",
        "end_date": "2026-04-03",
        **overrides,
    }


async def _create_absence(client: AsyncClient, employee: Employee, **overrides) -> dict:
    response = await client.post(
        "/absences/", json=_absence_payload(employee, **overrides)
    )
    assert response.status_code == 201
    return response.json()


# --- auth / permissions ---


@pytest.mark.asyncio
async def test_list_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/absences/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_requires_admin(authenticated_client: AsyncClient) -> None:
    response = await authenticated_client.get("/absences/")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_requires_auth(client: AsyncClient) -> None:
    response = await client.post("/absences/", json={})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_requires_admin(authenticated_client: AsyncClient) -> None:
    response = await authenticated_client.post("/absences/", json={})
    assert response.status_code == 403


# --- list ---


@pytest.mark.asyncio
async def test_list_empty(admin_client: AsyncClient) -> None:
    response = await admin_client.get("/absences/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_absences(admin_client: AsyncClient, employee: Employee) -> None:
    await _create_absence(admin_client, employee)
    response = await admin_client.get("/absences/")
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_list_filter_by_employee(
    admin_client: AsyncClient, employee: Employee, employee2: Employee
) -> None:
    await _create_absence(admin_client, employee)
    await _create_absence(
        admin_client, employee2, start_date="2026-05-01", end_date="2026-05-03"
    )

    response = await admin_client.get(f"/absences/?employee_id={employee.id}")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["employee_id"] == str(employee.id)


@pytest.mark.asyncio
async def test_list_filter_by_type(
    admin_client: AsyncClient, employee: Employee
) -> None:
    await _create_absence(admin_client, employee, absence_type="sick")
    await _create_absence(
        admin_client,
        employee,
        absence_type="vacation",
        start_date="2026-05-01",
        end_date="2026-05-05",
    )

    response = await admin_client.get("/absences/?absence_type=vacation")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["absence_type"] == "vacation"


@pytest.mark.asyncio
async def test_list_filter_by_date_range(
    admin_client: AsyncClient, employee: Employee
) -> None:
    await _create_absence(
        admin_client, employee, start_date="2026-04-01", end_date="2026-04-03"
    )
    await _create_absence(
        admin_client, employee, start_date="2026-06-01", end_date="2026-06-05"
    )

    # Should find only the April absence
    response = await admin_client.get(
        "/absences/?date_from=2026-03-01&date_to=2026-04-30"
    )
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["start_date"] == "2026-04-01"


# --- create ---


@pytest.mark.asyncio
async def test_create_absence(admin_client: AsyncClient, employee: Employee) -> None:
    data = await _create_absence(admin_client, employee, notes="Flu", hours=24.0)
    assert data["employee_id"] == str(employee.id)
    assert data["absence_type"] == "sick"
    assert data["start_date"] == "2026-04-01"
    assert data["end_date"] == "2026-04-03"
    assert data["notes"] == "Flu"
    assert data["hours"] == 24.0
    assert data["employee"]["first_name"] == "Pelle"


@pytest.mark.asyncio
async def test_create_absence_all_types(
    admin_client: AsyncClient, employee: Employee
) -> None:
    """Every absence type should be creatable."""
    types = ["sick", "vab", "vacation", "parental_leave", "leave_of_absence"]
    for i, t in enumerate(types):
        start = f"2026-0{i + 1}-01"
        end = f"2026-0{i + 1}-05"
        data = await _create_absence(
            admin_client, employee, absence_type=t, start_date=start, end_date=end
        )
        assert data["absence_type"] == t


@pytest.mark.asyncio
async def test_create_absence_single_day(
    admin_client: AsyncClient, employee: Employee
) -> None:
    data = await _create_absence(
        admin_client, employee, start_date="2026-04-01", end_date="2026-04-01"
    )
    assert data["start_date"] == data["end_date"]


@pytest.mark.asyncio
async def test_create_absence_employee_not_found(admin_client: AsyncClient) -> None:
    response = await admin_client.post(
        "/absences/",
        json={
            "employee_id": str(uuid.uuid4()),
            "absence_type": "sick",
            "start_date": "2026-04-01",
            "end_date": "2026-04-03",
        },
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_absence_invalid_date_range(
    admin_client: AsyncClient, employee: Employee
) -> None:
    """start_date after end_date should fail."""
    response = await admin_client.post(
        "/absences/",
        json=_absence_payload(employee, start_date="2026-04-05", end_date="2026-04-01"),
    )
    assert response.status_code == 422


# --- overlap detection ---


@pytest.mark.asyncio
async def test_create_absence_overlap_exact(
    admin_client: AsyncClient, employee: Employee
) -> None:
    """Same dates for same employee should conflict."""
    await _create_absence(admin_client, employee)
    response = await admin_client.post("/absences/", json=_absence_payload(employee))
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_absence_overlap_partial(
    admin_client: AsyncClient, employee: Employee
) -> None:
    """Overlapping date range should conflict."""
    await _create_absence(
        admin_client, employee, start_date="2026-04-01", end_date="2026-04-05"
    )
    response = await admin_client.post(
        "/absences/",
        json=_absence_payload(employee, start_date="2026-04-03", end_date="2026-04-07"),
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_absence_overlap_contained(
    admin_client: AsyncClient, employee: Employee
) -> None:
    """New absence fully inside existing should conflict."""
    await _create_absence(
        admin_client, employee, start_date="2026-04-01", end_date="2026-04-10"
    )
    response = await admin_client.post(
        "/absences/",
        json=_absence_payload(employee, start_date="2026-04-03", end_date="2026-04-05"),
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_absence_adjacent_no_overlap(
    admin_client: AsyncClient, employee: Employee
) -> None:
    """Adjacent but non-overlapping absences should be allowed."""
    await _create_absence(
        admin_client, employee, start_date="2026-04-01", end_date="2026-04-03"
    )
    # Day after the first absence ends
    data = await _create_absence(
        admin_client, employee, start_date="2026-04-04", end_date="2026-04-06"
    )
    assert data["start_date"] == "2026-04-04"


@pytest.mark.asyncio
async def test_create_absence_different_employee_no_conflict(
    admin_client: AsyncClient, employee: Employee, employee2: Employee
) -> None:
    """Same dates, different employees — no conflict."""
    await _create_absence(admin_client, employee)
    data = await _create_absence(admin_client, employee2)
    assert data["employee_id"] == str(employee2.id)


# --- get ---


@pytest.mark.asyncio
async def test_get_absence(admin_client: AsyncClient, employee: Employee) -> None:
    created = await _create_absence(admin_client, employee)
    response = await admin_client.get(f"/absences/{created['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created["id"]
    assert data["employee"]["id"] == str(employee.id)


@pytest.mark.asyncio
async def test_get_absence_not_found(admin_client: AsyncClient) -> None:
    response = await admin_client.get(f"/absences/{uuid.uuid4()}")
    assert response.status_code == 404


# --- update ---


@pytest.mark.asyncio
async def test_update_absence(admin_client: AsyncClient, employee: Employee) -> None:
    created = await _create_absence(admin_client, employee)
    response = await admin_client.patch(
        f"/absences/{created['id']}",
        json={"absence_type": "vacation", "notes": "Summer break"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["absence_type"] == "vacation"
    assert data["notes"] == "Summer break"


@pytest.mark.asyncio
async def test_update_absence_dates(
    admin_client: AsyncClient, employee: Employee
) -> None:
    created = await _create_absence(admin_client, employee)
    response = await admin_client.patch(
        f"/absences/{created['id']}",
        json={"start_date": "2026-04-02", "end_date": "2026-04-04"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["start_date"] == "2026-04-02"
    assert data["end_date"] == "2026-04-04"


@pytest.mark.asyncio
async def test_update_absence_invalid_date_range(
    admin_client: AsyncClient, employee: Employee
) -> None:
    created = await _create_absence(admin_client, employee)
    response = await admin_client.patch(
        f"/absences/{created['id']}",
        json={"start_date": "2026-04-10", "end_date": "2026-04-01"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_absence_overlap(
    admin_client: AsyncClient, employee: Employee
) -> None:
    """Moving dates to overlap with another absence should fail."""
    await _create_absence(
        admin_client, employee, start_date="2026-04-01", end_date="2026-04-03"
    )
    second = await _create_absence(
        admin_client, employee, start_date="2026-04-10", end_date="2026-04-12"
    )
    # Try to move second absence to overlap with first
    response = await admin_client.patch(
        f"/absences/{second['id']}",
        json={"start_date": "2026-04-02"},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_update_absence_same_dates_no_self_conflict(
    admin_client: AsyncClient, employee: Employee
) -> None:
    """Updating non-date fields shouldn't trigger self-overlap."""
    created = await _create_absence(admin_client, employee)
    response = await admin_client.patch(
        f"/absences/{created['id']}",
        json={"notes": "Updated notes"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_update_absence_not_found(admin_client: AsyncClient) -> None:
    response = await admin_client.patch(f"/absences/{uuid.uuid4()}", json={"notes": "x"})
    assert response.status_code == 404


# --- delete ---


@pytest.mark.asyncio
async def test_delete_absence(admin_client: AsyncClient, employee: Employee) -> None:
    created = await _create_absence(admin_client, employee)
    response = await admin_client.delete(f"/absences/{created['id']}")
    assert response.status_code == 204

    response = await admin_client.get(f"/absences/{created['id']}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_absence_not_found(admin_client: AsyncClient) -> None:
    response = await admin_client.delete(f"/absences/{uuid.uuid4()}")
    assert response.status_code == 404
