"""Tests for permission checking logic: hierarchy, wildcard, admin bypass."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from models import ActionType, Permission, User
from permissions.repo import get_acceptable_actions, has_permission


# --- action hierarchy ---


def test_acceptable_actions_read() -> None:
    result = get_acceptable_actions(ActionType.READ)
    assert ActionType.READ in result
    assert ActionType.WRITE in result
    assert ActionType.ADMIN in result


def test_acceptable_actions_write() -> None:
    result = get_acceptable_actions(ActionType.WRITE)
    assert ActionType.READ not in result
    assert ActionType.WRITE in result
    assert ActionType.ADMIN in result


def test_acceptable_actions_admin() -> None:
    result = get_acceptable_actions(ActionType.ADMIN)
    assert ActionType.READ not in result
    assert ActionType.WRITE not in result
    assert ActionType.ADMIN in result


# --- has_permission ---


@pytest.mark.asyncio
async def test_no_permission(db: AsyncSession, user: User) -> None:
    result = await has_permission(
        db,
        user_id=user.id,
        resource="schedule:*",
        minimum_action=ActionType.READ,
    )
    assert result is False


@pytest.mark.asyncio
async def test_exact_permission(db: AsyncSession, admin_user: User) -> None:
    """Grant exact permission and verify it works."""
    perm = Permission(
        principal=f"user:{admin_user.id}",
        resource="schedule:*",
        action="read",
        created_by=admin_user.id,
    )
    db.add(perm)
    await db.commit()

    result = await has_permission(
        db,
        user_id=admin_user.id,
        resource="schedule:*",
        minimum_action=ActionType.READ,
    )
    assert result is True


@pytest.mark.asyncio
async def test_higher_action_satisfies_lower(db: AsyncSession, admin_user: User) -> None:
    """A 'write' permission should satisfy a 'read' requirement."""
    perm = Permission(
        principal=f"user:{admin_user.id}",
        resource="schedule:*",
        action="write",
        created_by=admin_user.id,
    )
    db.add(perm)
    await db.commit()

    result = await has_permission(
        db,
        user_id=admin_user.id,
        resource="schedule:*",
        minimum_action=ActionType.READ,
    )
    assert result is True


@pytest.mark.asyncio
async def test_lower_action_does_not_satisfy_higher(
    db: AsyncSession, admin_user: User
) -> None:
    """A 'read' permission should NOT satisfy a 'write' requirement."""
    perm = Permission(
        principal=f"user:{admin_user.id}",
        resource="schedule:*",
        action="read",
        created_by=admin_user.id,
    )
    db.add(perm)
    await db.commit()

    result = await has_permission(
        db,
        user_id=admin_user.id,
        resource="schedule:*",
        minimum_action=ActionType.WRITE,
    )
    assert result is False


@pytest.mark.asyncio
async def test_wildcard_covers_specific_resource(
    db: AsyncSession, admin_user: User
) -> None:
    """A 'schedule:*' permission should cover 'schedule:<specific-uuid>'."""
    perm = Permission(
        principal=f"user:{admin_user.id}",
        resource="schedule:*",
        action="read",
        created_by=admin_user.id,
    )
    db.add(perm)
    await db.commit()

    specific_id = uuid.uuid4()
    result = await has_permission(
        db,
        user_id=admin_user.id,
        resource=f"schedule:{specific_id}",
        minimum_action=ActionType.READ,
    )
    assert result is True


@pytest.mark.asyncio
async def test_specific_permission_does_not_grant_wildcard(
    db: AsyncSession, admin_user: User
) -> None:
    """A 'schedule:<uuid>' permission should NOT grant access to other schedules."""
    specific_id = uuid.uuid4()
    perm = Permission(
        principal=f"user:{admin_user.id}",
        resource=f"schedule:{specific_id}",
        action="read",
        created_by=admin_user.id,
    )
    db.add(perm)
    await db.commit()

    other_id = uuid.uuid4()
    result = await has_permission(
        db,
        user_id=admin_user.id,
        resource=f"schedule:{other_id}",
        minimum_action=ActionType.READ,
    )
    assert result is False


@pytest.mark.asyncio
async def test_wrong_user_has_no_access(db: AsyncSession, admin_user: User) -> None:
    """A permission for user A should not grant access to user B."""
    other_user_id = uuid.uuid4()
    perm = Permission(
        principal=f"user:{other_user_id}",
        resource="schedule:*",
        action="admin",
        created_by=admin_user.id,
    )
    db.add(perm)
    await db.commit()

    result = await has_permission(
        db,
        user_id=admin_user.id,
        resource="schedule:*",
        minimum_action=ActionType.READ,
    )
    assert result is False
