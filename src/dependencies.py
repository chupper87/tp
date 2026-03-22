from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db as get_db
from idp.core import get_authenticated_admin_user as get_authenticated_admin_user
from idp.core import get_authenticated_user as get_authenticated_user
from log_setup import get_logger
from models import Base, Employee, User

log = get_logger(__name__)


async def get_current_employee(
    user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
) -> Employee:
    """
    Resolve the authenticated user's linked Employee record.

    Raises 403 if the user has no employee profile (e.g. pure admin accounts).
    This is used by public API endpoints where employees view their own data.
    """
    result = await db.execute(select(Employee).where(Employee.user_id == user.id))
    employee = result.scalar_one_or_none()
    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No employee profile linked to this user",
        )
    return employee


def get_model_by_id_or_404(model: type[Base]):
    """
    Returns a FastAPI dependency that fetches a model instance by its primary key
    from the path parameter, or raises 404 if not found.

    Usage:
        @router.get("/{id}")
        async def get_item(item = Depends(get_model_by_id_or_404(MyModel))):
            ...
    """

    async def inner(id: str, db: AsyncSession = Depends(get_db)) -> Base:
        from uuid import UUID

        try:
            uuid = UUID(id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid UUID: {id}",
            )

        instance = await db.get(model, uuid)
        if instance is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{model.__name__} not found",
            )
        return instance

    return inner
