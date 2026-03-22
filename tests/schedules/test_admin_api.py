from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models import Absence, Customer, Employee, Measure, Schedule


def _schedule_payload(**overrides) -> dict:
    return {"date": "2026-04-01", "shift_type": "morning", **overrides}


# --- auth / permissions ---


@pytest.mark.asyncio
async def test_list_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/schedules/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_requires_admin(authenticated_client: AsyncClient) -> None:
    response = await authenticated_client.get("/schedules/")
    assert response.status_code == 403


# --- list ---


@pytest.mark.asyncio
async def test_list_schedules_empty(admin_client: AsyncClient) -> None:
    response = await admin_client.get("/schedules/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_schedules(admin_client: AsyncClient, db: AsyncSession) -> None:
    db.add(Schedule(date=date(2026, 4, 1), shift_type="morning"))
    db.add(Schedule(date=date(2026, 4, 1), shift_type="evening"))
    await db.commit()
    response = await admin_client.get("/schedules/")
    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.asyncio
async def test_list_schedules_filter_by_shift_type(
    admin_client: AsyncClient, db: AsyncSession
) -> None:
    db.add(Schedule(date=date(2026, 4, 1), shift_type="morning"))
    db.add(Schedule(date=date(2026, 4, 1), shift_type="evening"))
    await db.commit()
    response = await admin_client.get("/schedules/?shift_type=morning")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["shift_type"] == "morning"


@pytest.mark.asyncio
async def test_list_schedules_filter_by_date_range(
    admin_client: AsyncClient, db: AsyncSession
) -> None:
    db.add(Schedule(date=date(2026, 4, 1), shift_type="morning"))
    db.add(Schedule(date=date(2026, 4, 10), shift_type="morning"))
    await db.commit()
    response = await admin_client.get(
        "/schedules/?date_from=2026-04-05&date_to=2026-04-15"
    )
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["date"] == "2026-04-10"


# --- create ---


@pytest.mark.asyncio
async def test_create_schedule_standard_shift(admin_client: AsyncClient) -> None:
    response = await admin_client.post("/schedules/", json=_schedule_payload())
    assert response.status_code == 201
    data = response.json()
    assert data["shift_type"] == "morning"
    assert data["date"] == "2026-04-01"
    assert data["employees"] == []
    assert data["customers"] == []
    assert data["measures"] == []


@pytest.mark.asyncio
async def test_create_schedule_custom_shift(admin_client: AsyncClient) -> None:
    response = await admin_client.post(
        "/schedules/", json={"date": "2026-04-01", "custom_shift": "Pelle 3h"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["shift_type"] is None
    assert data["custom_shift"] == "Pelle 3h"


@pytest.mark.asyncio
async def test_create_schedule_missing_shift_returns_422(
    admin_client: AsyncClient,
) -> None:
    response = await admin_client.post("/schedules/", json={"date": "2026-04-01"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_schedule_duplicate_standard_shift_returns_409(
    admin_client: AsyncClient,
) -> None:
    await admin_client.post("/schedules/", json=_schedule_payload())
    response = await admin_client.post("/schedules/", json=_schedule_payload())
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_schedule_two_custom_shifts_same_date_allowed(
    admin_client: AsyncClient,
) -> None:
    payload = {"date": "2026-04-01", "custom_shift": "Pelle 3h"}
    r1 = await admin_client.post("/schedules/", json=payload)
    r2 = await admin_client.post("/schedules/", json=payload)
    assert r1.status_code == 201
    assert r2.status_code == 201


# --- get ---


@pytest.mark.asyncio
async def test_get_schedule(admin_client: AsyncClient, schedule: Schedule) -> None:
    response = await admin_client.get(f"/schedules/{schedule.id}")
    assert response.status_code == 200
    assert response.json()["id"] == str(schedule.id)


@pytest.mark.asyncio
async def test_get_nonexistent_schedule(admin_client: AsyncClient) -> None:
    response = await admin_client.get("/schedules/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


# --- update ---


@pytest.mark.asyncio
async def test_update_schedule(admin_client: AsyncClient, schedule: Schedule) -> None:
    response = await admin_client.patch(
        f"/schedules/{schedule.id}", json={"shift_type": "evening"}
    )
    assert response.status_code == 200
    assert response.json()["shift_type"] == "evening"
    assert response.json()["date"] == "2026-04-01"  # unchanged


@pytest.mark.asyncio
async def test_update_schedule_conflict(
    admin_client: AsyncClient, db: AsyncSession, schedule: Schedule
) -> None:
    db.add(Schedule(date=date(2026, 4, 1), shift_type="evening"))
    await db.commit()
    response = await admin_client.patch(
        f"/schedules/{schedule.id}", json={"shift_type": "evening"}
    )
    assert response.status_code == 409


# --- assign / remove employee ---


@pytest.mark.asyncio
async def test_assign_employee(
    admin_client: AsyncClient, schedule: Schedule, employee: Employee
) -> None:
    response = await admin_client.post(
        f"/schedules/{schedule.id}/employees",
        json={"employee_id": str(employee.id)},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["employee_id"] == str(employee.id)
    assert data["employee"]["first_name"] == "Pelle"


@pytest.mark.asyncio
async def test_assign_nonexistent_employee_returns_404(
    admin_client: AsyncClient, schedule: Schedule
) -> None:
    response = await admin_client.post(
        f"/schedules/{schedule.id}/employees",
        json={"employee_id": "00000000-0000-0000-0000-000000000000"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_assign_employee_twice_returns_409(
    admin_client: AsyncClient, schedule: Schedule, employee: Employee
) -> None:
    payload = {"employee_id": str(employee.id)}
    await admin_client.post(f"/schedules/{schedule.id}/employees", json=payload)
    response = await admin_client.post(
        f"/schedules/{schedule.id}/employees", json=payload
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_assign_employee_with_absence_returns_409(
    admin_client: AsyncClient,
    schedule: Schedule,
    employee: Employee,
    db: AsyncSession,
) -> None:
    """Assigning an employee who has an absence covering the schedule date should 409."""
    db.add(
        Absence(
            employee_id=employee.id,
            absence_type="sick",
            start_date=date(2026, 3, 30),
            end_date=date(2026, 4, 5),
        )
    )
    await db.commit()

    response = await admin_client.post(
        f"/schedules/{schedule.id}/employees",
        json={"employee_id": str(employee.id)},
    )
    assert response.status_code == 409
    assert "absence" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_assign_employee_with_non_overlapping_absence_succeeds(
    admin_client: AsyncClient,
    schedule: Schedule,
    employee: Employee,
    db: AsyncSession,
) -> None:
    """An absence that does NOT cover the schedule date should not block assignment."""
    db.add(
        Absence(
            employee_id=employee.id,
            absence_type="vacation",
            start_date=date(2026, 5, 1),
            end_date=date(2026, 5, 10),
        )
    )
    await db.commit()

    response = await admin_client.post(
        f"/schedules/{schedule.id}/employees",
        json={"employee_id": str(employee.id)},
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_assign_employee_absence_starts_on_schedule_date_returns_409(
    admin_client: AsyncClient,
    schedule: Schedule,
    employee: Employee,
    db: AsyncSession,
) -> None:
    """Absence starting exactly on the schedule date should block."""
    db.add(
        Absence(
            employee_id=employee.id,
            absence_type="sick",
            start_date=date(2026, 4, 1),
            end_date=date(2026, 4, 1),
        )
    )
    await db.commit()

    response = await admin_client.post(
        f"/schedules/{schedule.id}/employees",
        json={"employee_id": str(employee.id)},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_assign_employee_absence_ends_before_schedule_date_succeeds(
    admin_client: AsyncClient,
    schedule: Schedule,
    employee: Employee,
    db: AsyncSession,
) -> None:
    """Absence ending the day before the schedule date should NOT block."""
    db.add(
        Absence(
            employee_id=employee.id,
            absence_type="sick",
            start_date=date(2026, 3, 25),
            end_date=date(2026, 3, 31),
        )
    )
    await db.commit()

    response = await admin_client.post(
        f"/schedules/{schedule.id}/employees",
        json={"employee_id": str(employee.id)},
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_remove_employee(
    admin_client: AsyncClient, schedule: Schedule, employee: Employee
) -> None:
    await admin_client.post(
        f"/schedules/{schedule.id}/employees",
        json={"employee_id": str(employee.id)},
    )
    response = await admin_client.delete(
        f"/schedules/{schedule.id}/employees/{employee.id}"
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_remove_employee_not_on_schedule_returns_404(
    admin_client: AsyncClient, schedule: Schedule, employee: Employee
) -> None:
    response = await admin_client.delete(
        f"/schedules/{schedule.id}/employees/{employee.id}"
    )
    assert response.status_code == 404


# --- assign / remove customer ---


@pytest.mark.asyncio
async def test_assign_customer(
    admin_client: AsyncClient, schedule: Schedule, customer: Customer
) -> None:
    response = await admin_client.post(
        f"/schedules/{schedule.id}/customers",
        json={"customer_id": str(customer.id)},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["customer_id"] == str(customer.id)
    assert data["customer"]["first_name"] == "Birgitta"


@pytest.mark.asyncio
async def test_assign_nonexistent_customer_returns_404(
    admin_client: AsyncClient, schedule: Schedule
) -> None:
    response = await admin_client.post(
        f"/schedules/{schedule.id}/customers",
        json={"customer_id": "00000000-0000-0000-0000-000000000000"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_assign_customer_twice_returns_409(
    admin_client: AsyncClient, schedule: Schedule, customer: Customer
) -> None:
    payload = {"customer_id": str(customer.id)}
    await admin_client.post(f"/schedules/{schedule.id}/customers", json=payload)
    response = await admin_client.post(
        f"/schedules/{schedule.id}/customers", json=payload
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_remove_customer(
    admin_client: AsyncClient, schedule: Schedule, customer: Customer
) -> None:
    await admin_client.post(
        f"/schedules/{schedule.id}/customers",
        json={"customer_id": str(customer.id)},
    )
    response = await admin_client.delete(
        f"/schedules/{schedule.id}/customers/{customer.id}"
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_remove_customer_not_on_schedule_returns_404(
    admin_client: AsyncClient, schedule: Schedule, customer: Customer
) -> None:
    response = await admin_client.delete(
        f"/schedules/{schedule.id}/customers/{customer.id}"
    )
    assert response.status_code == 404


# --- planned measures ---


@pytest.mark.asyncio
async def test_add_measure(
    admin_client: AsyncClient,
    schedule: Schedule,
    customer: Customer,
    measure: Measure,
) -> None:
    await admin_client.post(
        f"/schedules/{schedule.id}/customers",
        json={"customer_id": str(customer.id)},
    )
    response = await admin_client.post(
        f"/schedules/{schedule.id}/measures",
        json={
            "customer_id": str(customer.id),
            "measure_id": str(measure.id),
            "time_of_day": "night",
            "custom_duration": 15,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["customer_id"] == str(customer.id)
    assert data["measure_id"] == str(measure.id)
    assert data["time_of_day"] == "night"
    assert data["custom_duration"] == 15


@pytest.mark.asyncio
async def test_add_measure_customer_not_on_schedule_returns_409(
    admin_client: AsyncClient,
    schedule: Schedule,
    customer: Customer,
    measure: Measure,
) -> None:
    response = await admin_client.post(
        f"/schedules/{schedule.id}/measures",
        json={"customer_id": str(customer.id), "measure_id": str(measure.id)},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_add_measure_nonexistent_measure_returns_404(
    admin_client: AsyncClient, schedule: Schedule, customer: Customer
) -> None:
    await admin_client.post(
        f"/schedules/{schedule.id}/customers",
        json={"customer_id": str(customer.id)},
    )
    response = await admin_client.post(
        f"/schedules/{schedule.id}/measures",
        json={
            "customer_id": str(customer.id),
            "measure_id": "00000000-0000-0000-0000-000000000000",
        },
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_add_measure_duplicate_returns_409(
    admin_client: AsyncClient,
    schedule: Schedule,
    customer: Customer,
    measure: Measure,
) -> None:
    await admin_client.post(
        f"/schedules/{schedule.id}/customers",
        json={"customer_id": str(customer.id)},
    )
    payload = {
        "customer_id": str(customer.id),
        "measure_id": str(measure.id),
    }
    await admin_client.post(f"/schedules/{schedule.id}/measures", json=payload)
    response = await admin_client.post(
        f"/schedules/{schedule.id}/measures", json=payload
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_update_measure(
    admin_client: AsyncClient,
    schedule: Schedule,
    customer: Customer,
    measure: Measure,
) -> None:
    await admin_client.post(
        f"/schedules/{schedule.id}/customers",
        json={"customer_id": str(customer.id)},
    )
    r = await admin_client.post(
        f"/schedules/{schedule.id}/measures",
        json={"customer_id": str(customer.id), "measure_id": str(measure.id)},
    )
    sm_id = r.json()["id"]
    response = await admin_client.patch(
        f"/schedules/{schedule.id}/measures/{sm_id}",
        json={"time_of_day": "night", "custom_duration": 20},
    )
    assert response.status_code == 200
    assert response.json()["time_of_day"] == "night"
    assert response.json()["custom_duration"] == 20


@pytest.mark.asyncio
async def test_remove_measure(
    admin_client: AsyncClient,
    schedule: Schedule,
    customer: Customer,
    measure: Measure,
) -> None:
    await admin_client.post(
        f"/schedules/{schedule.id}/customers",
        json={"customer_id": str(customer.id)},
    )
    r = await admin_client.post(
        f"/schedules/{schedule.id}/measures",
        json={"customer_id": str(customer.id), "measure_id": str(measure.id)},
    )
    sm_id = r.json()["id"]
    response = await admin_client.delete(f"/schedules/{schedule.id}/measures/{sm_id}")
    assert response.status_code == 204


# --- schedule detail includes sub-resources ---


@pytest.mark.asyncio
async def test_get_schedule_detail_includes_assignments(
    admin_client: AsyncClient,
    schedule: Schedule,
    employee: Employee,
    customer: Customer,
    measure: Measure,
) -> None:
    await admin_client.post(
        f"/schedules/{schedule.id}/employees",
        json={"employee_id": str(employee.id)},
    )
    await admin_client.post(
        f"/schedules/{schedule.id}/customers",
        json={"customer_id": str(customer.id)},
    )
    await admin_client.post(
        f"/schedules/{schedule.id}/measures",
        json={"customer_id": str(customer.id), "measure_id": str(measure.id)},
    )
    response = await admin_client.get(f"/schedules/{schedule.id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data["employees"]) == 1
    assert len(data["customers"]) == 1
    assert len(data["measures"]) == 1
    assert data["employees"][0]["employee"]["first_name"] == "Pelle"
    assert data["customers"][0]["customer"]["first_name"] == "Birgitta"
