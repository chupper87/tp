import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from customers.repo import create_customer
from customers.schemas import CustomerCreate


def _customer_payload(**overrides) -> dict:
    return {
        "first_name": "Erik",
        "last_name": "Svensson",
        "key_number": 101,
        "address": "Storgatan 1, Stockholm",
        "care_level": "high",
        "approved_hours": 14.0,
        **overrides,
    }


# --- auth / permissions ---


@pytest.mark.asyncio
async def test_list_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/customers/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_requires_admin(authenticated_client: AsyncClient) -> None:
    response = await authenticated_client.get("/customers/")
    assert response.status_code == 403


# --- list ---


@pytest.mark.asyncio
async def test_list_customers_empty(admin_client: AsyncClient) -> None:
    response = await admin_client.get("/customers/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_customers(admin_client: AsyncClient, db: AsyncSession) -> None:
    await create_customer(db, CustomerCreate(**_customer_payload()))
    response = await admin_client.get("/customers/")
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_list_customers_filter_by_care_level(
    admin_client: AsyncClient, db: AsyncSession
) -> None:
    await create_customer(
        db, CustomerCreate(**_customer_payload(key_number=101, care_level="high"))
    )
    await create_customer(
        db, CustomerCreate(**_customer_payload(key_number=102, care_level="low"))
    )
    response = await admin_client.get("/customers/?care_level=high")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["care_level"] == "high"


# --- create ---


@pytest.mark.asyncio
async def test_create_customer(admin_client: AsyncClient) -> None:
    response = await admin_client.post("/customers/", json=_customer_payload())
    assert response.status_code == 201
    data = response.json()
    assert data["first_name"] == "Erik"
    assert data["key_number"] == 101
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_create_customer_duplicate_key_number(
    admin_client: AsyncClient, db: AsyncSession
) -> None:
    await create_customer(db, CustomerCreate(**_customer_payload()))
    response = await admin_client.post("/customers/", json=_customer_payload())
    assert response.status_code == 409


# --- get ---


@pytest.mark.asyncio
async def test_get_customer(admin_client: AsyncClient, db: AsyncSession) -> None:
    customer = await create_customer(db, CustomerCreate(**_customer_payload()))
    response = await admin_client.get(f"/customers/{customer.id}")
    assert response.status_code == 200
    assert response.json()["id"] == str(customer.id)


@pytest.mark.asyncio
async def test_get_nonexistent_customer(admin_client: AsyncClient) -> None:
    response = await admin_client.get("/customers/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


# --- update ---


@pytest.mark.asyncio
async def test_update_customer(admin_client: AsyncClient, db: AsyncSession) -> None:
    customer = await create_customer(db, CustomerCreate(**_customer_payload()))
    response = await admin_client.patch(
        f"/customers/{customer.id}",
        json={"approved_hours": 21.0, "care_level": "medium"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["approved_hours"] == 21.0
    assert data["care_level"] == "medium"
    assert data["first_name"] == "Erik"  # unchanged


@pytest.mark.asyncio
async def test_update_key_number_conflict(
    admin_client: AsyncClient, db: AsyncSession
) -> None:
    await create_customer(db, CustomerCreate(**_customer_payload(key_number=101)))
    c2 = await create_customer(db, CustomerCreate(**_customer_payload(key_number=102)))
    response = await admin_client.patch(f"/customers/{c2.id}", json={"key_number": 101})
    assert response.status_code == 409
