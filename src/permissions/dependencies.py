import uuid
from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from idp.core import get_authenticated_user
from log_setup import get_logger
from models import ActionType, Base, User
from permissions.repo import has_permission

log = get_logger(__name__)


def require_permission(
    resource_model: type[Base],
    minimum_action: ActionType,
) -> Callable:
    """
    FastAPI dependency factory that loads a resource by ID and checks permission.

    Admin users (is_admin=True) bypass permission checks entirely.
    Non-admin users must have at least `minimum_action` on the resource.

    Returns the resource object if authorized.
    Returns 404 if the resource doesn't exist OR the user lacks permission
    (intentionally hides permission denial to avoid leaking resource existence).

    Usage:
        ScheduleWithReadPermission = Annotated[
            Schedule,
            Depends(require_permission(Schedule, ActionType.READ)),
        ]

        @router.get("/{schedule_id}")
        async def get_schedule(schedule: ScheduleWithReadPermission):
            ...
    """
    # Derive resource_type from the model's tablename (e.g. "schedules" -> "schedule")
    tablename: str = resource_model.__tablename__  # type: ignore[assignment]
    resource_type = tablename.rstrip("s") if tablename.endswith("s") else tablename

    async def dep(
        resource_id: uuid.UUID,
        db: AsyncSession = Depends(get_db),
        user: User = Depends(get_authenticated_user),
    ) -> Base:
        # Fetch the resource
        resource = await db.get(resource_model, resource_id)
        if resource is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{resource_model.__name__} not found",
            )

        # Admin bypass — superusers skip permission checks
        if user.is_admin:
            return resource

        # Check permission for non-admin users
        resource_string = f"{resource_type}:{resource_id}"
        allowed = await has_permission(
            db,
            user_id=user.id,
            resource=resource_string,
            minimum_action=minimum_action,
        )
        if not allowed:
            # Return 404 (not 403) to hide resource existence
            log.debug(
                "permission_denied",
                user_id=str(user.id),
                resource=resource_string,
                minimum_action=minimum_action,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{resource_model.__name__} not found",
            )

        return resource

    return dep
