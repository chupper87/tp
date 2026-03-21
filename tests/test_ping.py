import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_ping(client: AsyncClient) -> None:
    response = await client.get("/ping")
    assert response.status_code == 200
    assert response.json() == {"detail": "Pong!"}


@pytest.mark.asyncio
async def test_unauthenticated_me_returns_401(client: AsyncClient) -> None:
    response = await client.get("/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_authenticated_me_returns_user(
    authenticated_client: AsyncClient,
) -> None:
    response = await authenticated_client.get("/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "user@example.com"
    assert data["is_admin"] is False
