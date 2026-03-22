import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from log_setup import get_logger
from models import ActionType, Permission
from permissions.errors import PermissionDuplicate, PermissionNotFound

log = get_logger(__name__)

# Action hierarchy: admin > write > read.
# If minimum_action is "read", then "write" and "admin" also satisfy the check.
_ACTION_HIERARCHY: dict[str, list[str]] = {
    ActionType.READ: [ActionType.READ, ActionType.WRITE, ActionType.ADMIN],
    ActionType.WRITE: [ActionType.WRITE, ActionType.ADMIN],
    ActionType.ADMIN: [ActionType.ADMIN],
}


def get_acceptable_actions(minimum_action: ActionType) -> list[str]:
    """Return actions that satisfy the given minimum (inclusive of higher levels)."""
    return _ACTION_HIERARCHY[minimum_action]


async def has_permission(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    resource: str,
    minimum_action: ActionType,
) -> bool:
    """
    Check if a user has at least the minimum action level on a resource.

    Checks both specific resource ("schedule:<uuid>") and wildcard
    ("schedule:*") permissions.
    """
    acceptable = get_acceptable_actions(minimum_action)
    resource_type = resource.split(":")[0]
    wildcard = f"{resource_type}:*"

    principal = f"user:{user_id}"
    result = await db.execute(
        select(Permission.id).where(
            Permission.principal == principal,
            Permission.resource.in_([resource, wildcard]),
            Permission.action.in_(acceptable),
        )
    )
    return result.scalar_one_or_none() is not None


async def get_permission_or_404(
    db: AsyncSession, permission_id: uuid.UUID
) -> Permission:
    result = await db.execute(select(Permission).where(Permission.id == permission_id))
    perm = result.scalar_one_or_none()
    if perm is None:
        raise PermissionNotFound(permission_id)
    return perm


async def list_permissions(
    db: AsyncSession,
    *,
    resource: str | None = None,
    principal: str | None = None,
) -> list[Permission]:
    q = select(Permission)
    if resource is not None:
        q = q.where(Permission.resource == resource)
    if principal is not None:
        q = q.where(Permission.principal == principal)
    result = await db.execute(q.order_by(Permission.created_at))
    return list(result.scalars().all())


async def create_permission(
    db: AsyncSession,
    *,
    principal: str,
    resource: str,
    action: str,
    created_by: uuid.UUID,
) -> Permission:
    """Create a permission.

    Raises PermissionDuplicate if (principal, resource) already exists.
    """
    existing = await db.execute(
        select(Permission).where(
            Permission.principal == principal,
            Permission.resource == resource,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise PermissionDuplicate(principal, resource)

    perm = Permission(
        principal=principal,
        resource=resource,
        action=action,
        created_by=created_by,
    )
    db.add(perm)
    await db.commit()
    await db.refresh(perm)
    log.info(
        "created_permission",
        permission_id=str(perm.id),
        principal=principal,
        resource=resource,
        action=action,
    )
    return perm


async def update_permission(
    db: AsyncSession,
    permission: Permission,
    action: str,
) -> Permission:
    """Update a permission's action level (upgrade or downgrade)."""
    permission.action = action  # type: ignore[assignment]
    await db.commit()
    await db.refresh(permission)
    log.info(
        "updated_permission",
        permission_id=str(permission.id),
        action=action,
    )
    return permission


async def delete_permission(db: AsyncSession, permission: Permission) -> None:
    await db.delete(permission)
    await db.commit()
    log.info("deleted_permission", permission_id=str(permission.id))
