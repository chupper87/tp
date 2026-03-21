import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from measures.repo import create_measure
from measures.schemas import MeasureCreate


def _measure_payload(**overrides) -> dict:
    return {
        "name": "Shower",
        "default_duration": 30,
        "time_of_day": "morning",
        "time_flexibility": "fixed",
        "is_standard": True,
        **overrides,
    }


# --- auth / permissions ---


@pytest.mark.asyncio
async def test_list_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/measures/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_requires_admin(authenticated_client: AsyncClient) -> None:
    response = await authenticated_client.get("/measures/")
    assert response.status_code == 403


# --- list ---


@pytest.mark.asyncio
async def test_list_measures_empty(admin_client: AsyncClient) -> None:
    response = await admin_client.get("/measures/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_measures(admin_client: AsyncClient, db: AsyncSession) -> None:
    await create_measure(db, MeasureCreate(**_measure_payload()))
    response = await admin_client.get("/measures/")
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_list_measures_filter_by_time_of_day(
    admin_client: AsyncClient, db: AsyncSession
) -> None:
    await create_measure(
        db, MeasureCreate(**_measure_payload(name="Shower", time_of_day="morning"))
    )
    await create_measure(
        db, MeasureCreate(**_measure_payload(name="Dinner", time_of_day="evening"))
    )
    response = await admin_client.get("/measures/?time_of_day=morning")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Shower"


# --- create ---


@pytest.mark.asyncio
async def test_create_measure(admin_client: AsyncClient) -> None:
    response = await admin_client.post("/measures/", json=_measure_payload())
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Shower"
    assert data["default_duration"] == 30
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_create_measure_duplicate_name(
    admin_client: AsyncClient, db: AsyncSession
) -> None:
    await create_measure(db, MeasureCreate(**_measure_payload()))
    response = await admin_client.post("/measures/", json=_measure_payload())
    assert response.status_code == 409


# --- get ---


@pytest.mark.asyncio
async def test_get_measure(admin_client: AsyncClient, db: AsyncSession) -> None:
    measure = await create_measure(db, MeasureCreate(**_measure_payload()))
    response = await admin_client.get(f"/measures/{measure.id}")
    assert response.status_code == 200
    assert response.json()["id"] == str(measure.id)


@pytest.mark.asyncio
async def test_get_nonexistent_measure(admin_client: AsyncClient) -> None:
    response = await admin_client.get("/measures/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


# --- update ---


@pytest.mark.asyncio
async def test_update_measure(admin_client: AsyncClient, db: AsyncSession) -> None:
    measure = await create_measure(db, MeasureCreate(**_measure_payload()))
    response = await admin_client.patch(
        f"/measures/{measure.id}",
        json={"default_duration": 45, "is_standard": False},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["default_duration"] == 45
    assert data["is_standard"] is False
    assert data["name"] == "Shower"  # unchanged


@pytest.mark.asyncio
async def test_update_measure_name_conflict(
    admin_client: AsyncClient, db: AsyncSession
) -> None:
    await create_measure(db, MeasureCreate(**_measure_payload(name="Shower")))
    m2 = await create_measure(db, MeasureCreate(**_measure_payload(name="Breakfast")))
    response = await admin_client.patch(f"/measures/{m2.id}", json={"name": "Shower"})
    assert response.status_code == 409
