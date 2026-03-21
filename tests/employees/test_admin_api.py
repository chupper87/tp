import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from employees.repo import create_employee
from employees.schemas import EmployeeCreate


def _employee_payload(**overrides) -> dict:
    return {
        "email": "emp@example.com",
        "password": "password123",
        "first_name": "Anna",
        "last_name": "Lindqvist",
        "role": "care_assistant",
        "employment_type": "full_time",
        "employment_degree": 100,
        **overrides,
    }


# --- auth / permissions ---


@pytest.mark.asyncio
async def test_list_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/employees/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_requires_admin(authenticated_client: AsyncClient) -> None:
    response = await authenticated_client.get("/employees/")
    assert response.status_code == 403


# --- list ---


@pytest.mark.asyncio
async def test_list_employees_empty(admin_client: AsyncClient) -> None:
    response = await admin_client.get("/employees/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_employees(admin_client: AsyncClient, db: AsyncSession) -> None:
    await create_employee(db, EmployeeCreate(**_employee_payload()))
    response = await admin_client.get("/employees/")
    assert response.status_code == 200
    assert len(response.json()) == 1


# --- create ---


@pytest.mark.asyncio
async def test_create_employee(admin_client: AsyncClient) -> None:
    response = await admin_client.post("/employees/", json=_employee_payload())
    assert response.status_code == 201
    data = response.json()
    assert data["first_name"] == "Anna"
    assert data["last_name"] == "Lindqvist"
    assert data["user"]["email"] == "emp@example.com"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_create_employee_duplicate_email(
    admin_client: AsyncClient, db: AsyncSession
) -> None:
    await create_employee(db, EmployeeCreate(**_employee_payload()))
    response = await admin_client.post("/employees/", json=_employee_payload())
    assert response.status_code == 409


# --- get ---


@pytest.mark.asyncio
async def test_get_employee(admin_client: AsyncClient, db: AsyncSession) -> None:
    employee = await create_employee(db, EmployeeCreate(**_employee_payload()))
    response = await admin_client.get(f"/employees/{employee.id}")
    assert response.status_code == 200
    assert response.json()["id"] == str(employee.id)


@pytest.mark.asyncio
async def test_get_nonexistent_employee(admin_client: AsyncClient) -> None:
    response = await admin_client.get("/employees/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


# --- update ---


@pytest.mark.asyncio
async def test_update_employee(admin_client: AsyncClient, db: AsyncSession) -> None:
    employee = await create_employee(db, EmployeeCreate(**_employee_payload()))
    response = await admin_client.patch(
        f"/employees/{employee.id}",
        json={"first_name": "Britta", "employment_degree": 75},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "Britta"
    assert data["employment_degree"] == 75
    assert data["last_name"] == "Lindqvist"  # unchanged


@pytest.mark.asyncio
async def test_update_nonexistent_employee(admin_client: AsyncClient) -> None:
    response = await admin_client.patch(
        "/employees/00000000-0000-0000-0000-000000000000",
        json={"first_name": "Britta"},
    )
    assert response.status_code == 404
