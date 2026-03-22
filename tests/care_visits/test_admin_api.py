import uuid

import pytest
from httpx import AsyncClient

from models import Customer, Employee, Schedule


def _visit_payload(
    schedule: Schedule, customer: Customer, employee: Employee, **overrides
) -> dict:
    return {
        "schedule_id": str(schedule.id),
        "customer_id": str(customer.id),
        "duration": 30,
        "employees": [{"employee_id": str(employee.id), "is_primary": True}],
        **overrides,
    }


async def _create_visit(
    client: AsyncClient,
    schedule: Schedule,
    customer: Customer,
    employee: Employee,
    **overrides,
) -> dict:
    """Helper: create a visit and return the response JSON."""
    response = await client.post(
        "/care-visits/",
        json=_visit_payload(schedule, customer, employee, **overrides),
    )
    assert response.status_code == 201
    return response.json()


# --- auth / permissions ---


@pytest.mark.asyncio
async def test_list_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/care-visits/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_requires_admin(authenticated_client: AsyncClient) -> None:
    response = await authenticated_client.get("/care-visits/")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_requires_auth(client: AsyncClient) -> None:
    response = await client.post("/care-visits/", json={})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_requires_admin(authenticated_client: AsyncClient) -> None:
    response = await authenticated_client.post("/care-visits/", json={})
    assert response.status_code == 403


# --- list ---


@pytest.mark.asyncio
async def test_list_empty(admin_client: AsyncClient) -> None:
    response = await admin_client.get("/care-visits/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_with_visits(
    admin_client: AsyncClient,
    schedule_with_employee_and_customer: Schedule,
    employee: Employee,
    customer: Customer,
) -> None:
    await _create_visit(
        admin_client,
        schedule_with_employee_and_customer,
        customer,
        employee,
    )
    response = await admin_client.get("/care-visits/")
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_list_filter_by_schedule(
    admin_client: AsyncClient,
    schedule_with_employee_and_customer: Schedule,
    employee: Employee,
    customer: Customer,
) -> None:
    await _create_visit(
        admin_client,
        schedule_with_employee_and_customer,
        customer,
        employee,
    )
    # Filter with matching schedule_id
    response = await admin_client.get(
        f"/care-visits/?schedule_id={schedule_with_employee_and_customer.id}"
    )
    assert response.status_code == 200
    assert len(response.json()) == 1

    # Filter with non-matching schedule_id
    response = await admin_client.get(f"/care-visits/?schedule_id={uuid.uuid4()}")
    assert response.status_code == 200
    assert len(response.json()) == 0


@pytest.mark.asyncio
async def test_list_filter_by_status(
    admin_client: AsyncClient,
    schedule_with_employee_and_customer: Schedule,
    employee: Employee,
    customer: Customer,
) -> None:
    await _create_visit(
        admin_client,
        schedule_with_employee_and_customer,
        customer,
        employee,
    )
    response = await admin_client.get("/care-visits/?status_filter=planned")
    assert response.status_code == 200
    assert len(response.json()) == 1

    response = await admin_client.get("/care-visits/?status_filter=completed")
    assert response.status_code == 200
    assert len(response.json()) == 0


# --- create ---


@pytest.mark.asyncio
async def test_create_care_visit(
    admin_client: AsyncClient,
    schedule_with_employee_and_customer: Schedule,
    employee: Employee,
    customer: Customer,
) -> None:
    data = await _create_visit(
        admin_client,
        schedule_with_employee_and_customer,
        customer,
        employee,
        notes="First visit",
    )
    assert data["status"] == "planned"
    assert data["duration"] == 30
    assert data["notes"] == "First visit"
    assert data["schedule_id"] == str(schedule_with_employee_and_customer.id)
    assert data["customer_id"] == str(customer.id)
    assert data["date"] == "2026-04-01"
    assert len(data["employees"]) == 1
    assert data["employees"][0]["employee_id"] == str(employee.id)
    assert data["employees"][0]["is_primary"] is True
    assert data["customer"]["id"] == str(customer.id)
    assert data["customer"]["first_name"] == "Birgitta"


@pytest.mark.asyncio
async def test_create_care_visit_employee_not_on_schedule(
    admin_client: AsyncClient,
    schedule_with_employee_and_customer: Schedule,
    customer: Customer,
    employee2: Employee,
) -> None:
    """Employee2 is not on the schedule — should fail."""
    response = await admin_client.post(
        "/care-visits/",
        json=_visit_payload(schedule_with_employee_and_customer, customer, employee2),
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_care_visit_customer_not_on_schedule(
    admin_client: AsyncClient,
    schedule_with_employee: Schedule,
    employee: Employee,
    customer: Customer,
) -> None:
    """Customer is not on the schedule (only employee is) — should fail."""
    response = await admin_client.post(
        "/care-visits/",
        json=_visit_payload(schedule_with_employee, customer, employee),
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_care_visit_no_employees_422(
    admin_client: AsyncClient,
    schedule_with_employee_and_customer: Schedule,
    customer: Customer,
) -> None:
    """Must provide at least one employee."""
    response = await admin_client.post(
        "/care-visits/",
        json={
            "schedule_id": str(schedule_with_employee_and_customer.id),
            "customer_id": str(customer.id),
            "duration": 30,
            "employees": [],
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_care_visit_zero_duration_422(
    admin_client: AsyncClient,
    schedule_with_employee_and_customer: Schedule,
    customer: Customer,
    employee: Employee,
) -> None:
    response = await admin_client.post(
        "/care-visits/",
        json=_visit_payload(
            schedule_with_employee_and_customer,
            customer,
            employee,
            duration=0,
        ),
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_care_visit_double_bemanning(
    admin_client: AsyncClient,
    schedule_with_two_employees_and_customer: Schedule,
    employee: Employee,
    employee2: Employee,
    customer: Customer,
) -> None:
    """Create a visit with two employees (double bemanning)."""
    response = await admin_client.post(
        "/care-visits/",
        json={
            "schedule_id": str(schedule_with_two_employees_and_customer.id),
            "customer_id": str(customer.id),
            "duration": 45,
            "employees": [
                {"employee_id": str(employee.id), "is_primary": True},
                {"employee_id": str(employee2.id), "is_primary": False},
            ],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert len(data["employees"]) == 2
    emp_ids = {e["employee_id"] for e in data["employees"]}
    assert str(employee.id) in emp_ids
    assert str(employee2.id) in emp_ids


# --- get ---


@pytest.mark.asyncio
async def test_get_care_visit(
    admin_client: AsyncClient,
    schedule_with_employee_and_customer: Schedule,
    employee: Employee,
    customer: Customer,
) -> None:
    created = await _create_visit(
        admin_client,
        schedule_with_employee_and_customer,
        customer,
        employee,
    )
    response = await admin_client.get(f"/care-visits/{created['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created["id"]
    assert len(data["employees"]) == 1


@pytest.mark.asyncio
async def test_get_care_visit_not_found(admin_client: AsyncClient) -> None:
    response = await admin_client.get(f"/care-visits/{uuid.uuid4()}")
    assert response.status_code == 404


# --- update ---


@pytest.mark.asyncio
async def test_update_care_visit(
    admin_client: AsyncClient,
    schedule_with_employee_and_customer: Schedule,
    employee: Employee,
    customer: Customer,
) -> None:
    created = await _create_visit(
        admin_client,
        schedule_with_employee_and_customer,
        customer,
        employee,
    )
    response = await admin_client.patch(
        f"/care-visits/{created['id']}",
        json={"duration": 60, "notes": "Updated notes"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["duration"] == 60
    assert data["notes"] == "Updated notes"


@pytest.mark.asyncio
async def test_update_care_visit_not_found(admin_client: AsyncClient) -> None:
    response = await admin_client.patch(
        f"/care-visits/{uuid.uuid4()}", json={"duration": 60}
    )
    assert response.status_code == 404


# --- status transitions ---


@pytest.mark.asyncio
async def test_status_planned_to_completed(
    admin_client: AsyncClient,
    schedule_with_employee_and_customer: Schedule,
    employee: Employee,
    customer: Customer,
) -> None:
    created = await _create_visit(
        admin_client,
        schedule_with_employee_and_customer,
        customer,
        employee,
    )
    response = await admin_client.patch(
        f"/care-visits/{created['id']}/status",
        json={"status": "completed"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "completed"


@pytest.mark.asyncio
async def test_status_planned_to_canceled(
    admin_client: AsyncClient,
    schedule_with_employee_and_customer: Schedule,
    employee: Employee,
    customer: Customer,
) -> None:
    created = await _create_visit(
        admin_client,
        schedule_with_employee_and_customer,
        customer,
        employee,
    )
    response = await admin_client.patch(
        f"/care-visits/{created['id']}/status",
        json={"status": "canceled"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "canceled"


@pytest.mark.asyncio
async def test_status_planned_to_no_show(
    admin_client: AsyncClient,
    schedule_with_employee_and_customer: Schedule,
    employee: Employee,
    customer: Customer,
) -> None:
    created = await _create_visit(
        admin_client,
        schedule_with_employee_and_customer,
        customer,
        employee,
    )
    response = await admin_client.patch(
        f"/care-visits/{created['id']}/status",
        json={"status": "no_show"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "no_show"


@pytest.mark.asyncio
async def test_status_planned_to_partially_completed(
    admin_client: AsyncClient,
    schedule_with_employee_and_customer: Schedule,
    employee: Employee,
    customer: Customer,
) -> None:
    created = await _create_visit(
        admin_client,
        schedule_with_employee_and_customer,
        customer,
        employee,
    )
    response = await admin_client.patch(
        f"/care-visits/{created['id']}/status",
        json={"status": "partially_completed"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "partially_completed"


@pytest.mark.asyncio
async def test_status_partially_completed_to_completed(
    admin_client: AsyncClient,
    schedule_with_employee_and_customer: Schedule,
    employee: Employee,
    customer: Customer,
) -> None:
    created = await _create_visit(
        admin_client,
        schedule_with_employee_and_customer,
        customer,
        employee,
    )
    # planned → partially_completed
    await admin_client.patch(
        f"/care-visits/{created['id']}/status",
        json={"status": "partially_completed"},
    )
    # partially_completed → completed
    response = await admin_client.patch(
        f"/care-visits/{created['id']}/status",
        json={"status": "completed"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "completed"


@pytest.mark.asyncio
async def test_status_completed_is_terminal(
    admin_client: AsyncClient,
    schedule_with_employee_and_customer: Schedule,
    employee: Employee,
    customer: Customer,
) -> None:
    created = await _create_visit(
        admin_client,
        schedule_with_employee_and_customer,
        customer,
        employee,
    )
    # planned → completed
    await admin_client.patch(
        f"/care-visits/{created['id']}/status",
        json={"status": "completed"},
    )
    # completed → planned should fail
    response = await admin_client.patch(
        f"/care-visits/{created['id']}/status",
        json={"status": "planned"},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_status_canceled_to_planned(
    admin_client: AsyncClient,
    schedule_with_employee_and_customer: Schedule,
    employee: Employee,
    customer: Customer,
) -> None:
    created = await _create_visit(
        admin_client,
        schedule_with_employee_and_customer,
        customer,
        employee,
    )
    # planned → canceled
    await admin_client.patch(
        f"/care-visits/{created['id']}/status",
        json={"status": "canceled"},
    )
    # canceled → planned (re-activate)
    response = await admin_client.patch(
        f"/care-visits/{created['id']}/status",
        json={"status": "planned"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "planned"


@pytest.mark.asyncio
async def test_status_invalid_transition(
    admin_client: AsyncClient,
    schedule_with_employee_and_customer: Schedule,
    employee: Employee,
    customer: Customer,
) -> None:
    created = await _create_visit(
        admin_client,
        schedule_with_employee_and_customer,
        customer,
        employee,
    )
    # planned → planned is not a valid transition
    response = await admin_client.patch(
        f"/care-visits/{created['id']}/status",
        json={"status": "planned"},
    )
    assert response.status_code == 409


# --- delete ---


@pytest.mark.asyncio
async def test_delete_care_visit(
    admin_client: AsyncClient,
    schedule_with_employee_and_customer: Schedule,
    employee: Employee,
    customer: Customer,
) -> None:
    created = await _create_visit(
        admin_client,
        schedule_with_employee_and_customer,
        customer,
        employee,
    )
    response = await admin_client.delete(f"/care-visits/{created['id']}")
    assert response.status_code == 204

    # Verify it's gone
    response = await admin_client.get(f"/care-visits/{created['id']}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_care_visit_not_found(admin_client: AsyncClient) -> None:
    response = await admin_client.delete(f"/care-visits/{uuid.uuid4()}")
    assert response.status_code == 404


# --- employee assignment (double bemanning) ---


@pytest.mark.asyncio
async def test_add_employee_to_visit(
    admin_client: AsyncClient,
    schedule_with_two_employees_and_customer: Schedule,
    employee: Employee,
    employee2: Employee,
    customer: Customer,
) -> None:
    """Add a second employee to an existing visit (double bemanning)."""
    created = await _create_visit(
        admin_client,
        schedule_with_two_employees_and_customer,
        customer,
        employee,
    )
    assert len(created["employees"]) == 1

    response = await admin_client.post(
        f"/care-visits/{created['id']}/employees",
        json={
            "employee_id": str(employee2.id),
            "is_primary": False,
            "notes": "Second worker for heavy lift",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert len(data["employees"]) == 2


@pytest.mark.asyncio
async def test_add_employee_not_on_schedule(
    admin_client: AsyncClient,
    schedule_with_employee_and_customer: Schedule,
    employee: Employee,
    employee2: Employee,
    customer: Customer,
) -> None:
    """Employee2 is not on the schedule — cannot be added to visit."""
    created = await _create_visit(
        admin_client,
        schedule_with_employee_and_customer,
        customer,
        employee,
    )
    response = await admin_client.post(
        f"/care-visits/{created['id']}/employees",
        json={"employee_id": str(employee2.id)},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_add_employee_already_on_visit(
    admin_client: AsyncClient,
    schedule_with_employee_and_customer: Schedule,
    employee: Employee,
    customer: Customer,
) -> None:
    """Same employee cannot be added twice."""
    created = await _create_visit(
        admin_client,
        schedule_with_employee_and_customer,
        customer,
        employee,
    )
    response = await admin_client.post(
        f"/care-visits/{created['id']}/employees",
        json={"employee_id": str(employee.id)},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_remove_employee_from_visit(
    admin_client: AsyncClient,
    schedule_with_two_employees_and_customer: Schedule,
    employee: Employee,
    employee2: Employee,
    customer: Customer,
) -> None:
    """Remove one of two employees from a visit."""
    # Create visit with two employees
    response = await admin_client.post(
        "/care-visits/",
        json={
            "schedule_id": str(schedule_with_two_employees_and_customer.id),
            "customer_id": str(customer.id),
            "duration": 45,
            "employees": [
                {"employee_id": str(employee.id), "is_primary": True},
                {"employee_id": str(employee2.id), "is_primary": False},
            ],
        },
    )
    assert response.status_code == 201
    visit_id = response.json()["id"]

    # Remove employee2
    response = await admin_client.delete(
        f"/care-visits/{visit_id}/employees/{employee2.id}"
    )
    assert response.status_code == 204

    # Verify only one employee remains
    response = await admin_client.get(f"/care-visits/{visit_id}")
    assert len(response.json()["employees"]) == 1


@pytest.mark.asyncio
async def test_remove_last_employee_blocked(
    admin_client: AsyncClient,
    schedule_with_employee_and_customer: Schedule,
    employee: Employee,
    customer: Customer,
) -> None:
    """Cannot remove the only employee — visit must have at least one."""
    created = await _create_visit(
        admin_client,
        schedule_with_employee_and_customer,
        customer,
        employee,
    )
    response = await admin_client.delete(
        f"/care-visits/{created['id']}/employees/{employee.id}"
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_remove_employee_not_on_visit(
    admin_client: AsyncClient,
    schedule_with_two_employees_and_customer: Schedule,
    employee: Employee,
    employee2: Employee,
    customer: Customer,
) -> None:
    """Removing an employee that's not on the visit returns 404."""
    created = await _create_visit(
        admin_client,
        schedule_with_two_employees_and_customer,
        customer,
        employee,
    )
    response = await admin_client.delete(
        f"/care-visits/{created['id']}/employees/{employee2.id}"
    )
    assert response.status_code == 404
