import pytest
from httpx import AsyncClient

from models import Customer, Employee


# --- auth ---


@pytest.mark.asyncio
async def test_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/audit/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_requires_admin(authenticated_client: AsyncClient) -> None:
    response = await authenticated_client.get("/audit/")
    assert response.status_code == 403


# --- empty ---


@pytest.mark.asyncio
async def test_list_empty(admin_client: AsyncClient) -> None:
    response = await admin_client.get("/audit/")
    assert response.status_code == 200
    assert response.json() == []


# --- audit entries created by mutations ---


@pytest.mark.asyncio
async def test_customer_create_audited(
    admin_client: AsyncClient,
) -> None:
    resp = await admin_client.post(
        "/customers/",
        json={
            "first_name": "Test",
            "last_name": "Person",
            "key_number": 9999,
            "address": "Testgatan 1",
        },
    )
    assert resp.status_code == 201
    customer_id = resp.json()["id"]

    audit_resp = await admin_client.get("/audit/?resource_type=customer")
    assert audit_resp.status_code == 200
    entries = audit_resp.json()
    assert len(entries) == 1
    assert entries[0]["action"] == "created"
    assert entries[0]["resource_type"] == "customer"
    assert entries[0]["resource_id"] == customer_id


@pytest.mark.asyncio
async def test_customer_update_audited(
    admin_client: AsyncClient, customer: Customer
) -> None:
    resp = await admin_client.patch(
        f"/customers/{customer.id}",
        json={"approved_hours": 50.0},
    )
    assert resp.status_code == 200

    audit_resp = await admin_client.get(
        f"/audit/?resource_type=customer&resource_id={customer.id}"
    )
    entries = audit_resp.json()
    assert len(entries) == 1
    assert entries[0]["action"] == "updated"
    assert entries[0]["changes"]["approved_hours"] == 50.0


@pytest.mark.asyncio
async def test_employee_create_audited(admin_client: AsyncClient) -> None:
    resp = await admin_client.post(
        "/employees/",
        json={
            "first_name": "Nils",
            "last_name": "Nilsson",
            "email": "nils@test.com",
            "password": "password123",
        },
    )
    assert resp.status_code == 201

    audit_resp = await admin_client.get("/audit/?resource_type=employee")
    entries = audit_resp.json()
    assert len(entries) == 1
    assert entries[0]["action"] == "created"


@pytest.mark.asyncio
async def test_absence_lifecycle_audited(
    admin_client: AsyncClient, employee: Employee
) -> None:
    """Create, update, delete should each produce an audit entry."""
    # Create
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

    # Update
    resp = await admin_client.patch(
        f"/absences/{absence_id}",
        json={"notes": "Flu"},
    )
    assert resp.status_code == 200

    # Delete
    resp = await admin_client.delete(f"/absences/{absence_id}")
    assert resp.status_code == 204

    audit_resp = await admin_client.get("/audit/?resource_type=absence")
    entries = audit_resp.json()
    assert len(entries) == 3
    actions = [e["action"] for e in entries]
    # Entries are newest-first
    assert "created" in actions
    assert "updated" in actions
    assert "deleted" in actions


# --- filter by resource_id ---


@pytest.mark.asyncio
async def test_filter_by_resource_id(
    admin_client: AsyncClient, customer: Customer
) -> None:
    # Create two customers, audit both
    resp1 = await admin_client.post(
        "/customers/",
        json={
            "first_name": "A",
            "last_name": "B",
            "key_number": 8001,
            "address": "X",
        },
    )
    assert resp1.status_code == 201
    id1 = resp1.json()["id"]

    resp2 = await admin_client.post(
        "/customers/",
        json={
            "first_name": "C",
            "last_name": "D",
            "key_number": 8002,
            "address": "Y",
        },
    )
    assert resp2.status_code == 201

    # Filter by first customer
    audit_resp = await admin_client.get(
        f"/audit/?resource_type=customer&resource_id={id1}"
    )
    entries = audit_resp.json()
    assert len(entries) == 1
    assert entries[0]["resource_id"] == id1


# --- filter by date ---


@pytest.mark.asyncio
async def test_filter_by_date(admin_client: AsyncClient) -> None:
    resp = await admin_client.post(
        "/customers/",
        json={
            "first_name": "A",
            "last_name": "B",
            "key_number": 7001,
            "address": "Z",
        },
    )
    assert resp.status_code == 201

    # Future date should find nothing
    audit_resp = await admin_client.get("/audit/?date_from=2099-01-01")
    assert audit_resp.json() == []

    # Today should find it
    audit_resp = await admin_client.get("/audit/?date_from=2026-01-01")
    assert len(audit_resp.json()) >= 1


# --- schedule create audited ---


@pytest.mark.asyncio
async def test_schedule_create_audited(admin_client: AsyncClient) -> None:
    resp = await admin_client.post(
        "/schedules/",
        json={"date": "2026-05-01", "shift_type": "morning"},
    )
    assert resp.status_code == 201

    audit_resp = await admin_client.get("/audit/?resource_type=schedule")
    entries = audit_resp.json()
    assert len(entries) == 1
    assert entries[0]["action"] == "created"
