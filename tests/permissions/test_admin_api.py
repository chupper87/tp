import uuid

import pytest
from httpx import AsyncClient

from models import User


def _perm_payload(**overrides) -> dict:
    return {
        "principal": f"user:{uuid.uuid4()}",
        "resource": "schedule:*",
        "action": "read",
        **overrides,
    }


async def _create_perm(client: AsyncClient, **overrides) -> dict:
    response = await client.post("/permissions/", json=_perm_payload(**overrides))
    assert response.status_code == 201
    return response.json()


# --- auth ---


@pytest.mark.asyncio
async def test_list_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/permissions/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_requires_admin(authenticated_client: AsyncClient) -> None:
    response = await authenticated_client.get("/permissions/")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_requires_admin(authenticated_client: AsyncClient) -> None:
    response = await authenticated_client.post("/permissions/", json=_perm_payload())
    assert response.status_code == 403


# --- list ---


@pytest.mark.asyncio
async def test_list_empty(admin_client: AsyncClient) -> None:
    response = await admin_client.get("/permissions/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_permissions(admin_client: AsyncClient) -> None:
    await _create_perm(admin_client)
    response = await admin_client.get("/permissions/")
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_list_filter_by_resource(admin_client: AsyncClient) -> None:
    await _create_perm(admin_client, resource="schedule:*")
    await _create_perm(
        admin_client,
        principal=f"user:{uuid.uuid4()}",
        resource="customer:*",
    )

    response = await admin_client.get("/permissions/?resource=schedule:*")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["resource"] == "schedule:*"


@pytest.mark.asyncio
async def test_list_filter_by_principal(admin_client: AsyncClient) -> None:
    uid = str(uuid.uuid4())
    await _create_perm(admin_client, principal=f"user:{uid}", resource="schedule:*")
    await _create_perm(
        admin_client,
        principal=f"user:{uuid.uuid4()}",
        resource="customer:*",
    )

    response = await admin_client.get(f"/permissions/?principal=user:{uid}")
    assert response.status_code == 200
    assert len(response.json()) == 1


# --- create ---


@pytest.mark.asyncio
async def test_create_permission(admin_client: AsyncClient, admin_user: User) -> None:
    data = await _create_perm(
        admin_client,
        principal="user:00000000-0000-0000-0000-000000000001",
        resource="schedule:*",
        action="write",
    )
    assert data["principal"] == "user:00000000-0000-0000-0000-000000000001"
    assert data["resource"] == "schedule:*"
    assert data["action"] == "write"
    assert data["created_by"] == str(admin_user.id)
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_permission_specific_resource(admin_client: AsyncClient) -> None:
    rid = str(uuid.uuid4())
    data = await _create_perm(admin_client, resource=f"schedule:{rid}")
    assert data["resource"] == f"schedule:{rid}"


@pytest.mark.asyncio
async def test_create_permission_duplicate(admin_client: AsyncClient) -> None:
    payload = _perm_payload()
    resp1 = await admin_client.post("/permissions/", json=payload)
    assert resp1.status_code == 201

    resp2 = await admin_client.post("/permissions/", json=payload)
    assert resp2.status_code == 409


# --- get ---


@pytest.mark.asyncio
async def test_get_permission(admin_client: AsyncClient) -> None:
    created = await _create_perm(admin_client)
    response = await admin_client.get(f"/permissions/{created['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


@pytest.mark.asyncio
async def test_get_permission_not_found(admin_client: AsyncClient) -> None:
    response = await admin_client.get(f"/permissions/{uuid.uuid4()}")
    assert response.status_code == 404


# --- update (change action level) ---


@pytest.mark.asyncio
async def test_update_permission_action(admin_client: AsyncClient) -> None:
    created = await _create_perm(admin_client, action="read")
    response = await admin_client.patch(
        f"/permissions/{created['id']}", json={"action": "admin"}
    )
    assert response.status_code == 200
    assert response.json()["action"] == "admin"


@pytest.mark.asyncio
async def test_update_permission_downgrade(admin_client: AsyncClient) -> None:
    created = await _create_perm(admin_client, action="admin")
    response = await admin_client.patch(
        f"/permissions/{created['id']}", json={"action": "read"}
    )
    assert response.status_code == 200
    assert response.json()["action"] == "read"


@pytest.mark.asyncio
async def test_update_permission_not_found(admin_client: AsyncClient) -> None:
    response = await admin_client.patch(
        f"/permissions/{uuid.uuid4()}", json={"action": "write"}
    )
    assert response.status_code == 404


# --- delete ---


@pytest.mark.asyncio
async def test_delete_permission(admin_client: AsyncClient) -> None:
    created = await _create_perm(admin_client)
    response = await admin_client.delete(f"/permissions/{created['id']}")
    assert response.status_code == 204

    response = await admin_client.get(f"/permissions/{created['id']}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_permission_not_found(admin_client: AsyncClient) -> None:
    response = await admin_client.delete(f"/permissions/{uuid.uuid4()}")
    assert response.status_code == 404
