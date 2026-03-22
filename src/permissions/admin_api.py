import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from api_core import responses_from_api_errors
from dependencies import get_authenticated_admin_user, get_db
from models import Permission, User
from permissions import repo
from permissions.errors import PermissionDuplicateError, PermissionNotFoundError
from permissions.schemas import PermissionCreate, PermissionOut, PermissionUpdate

router = APIRouter(tags=["Permissions (admin)"])


@router.get("/", response_model=list[PermissionOut])
async def list_permissions(
    resource: Optional[str] = None,
    principal: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_authenticated_admin_user),
) -> list[Permission]:
    return await repo.list_permissions(db, resource=resource, principal=principal)


@router.post(
    "/",
    response_model=PermissionOut,
    status_code=status.HTTP_201_CREATED,
    responses=responses_from_api_errors(PermissionDuplicateError),
)
async def create_permission(
    data: PermissionCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_authenticated_admin_user),
) -> Permission:
    return await repo.create_permission(
        db,
        principal=data.principal,
        resource=data.resource,
        action=data.action,
        created_by=admin.id,
    )


@router.get(
    "/{permission_id}",
    response_model=PermissionOut,
    responses=responses_from_api_errors(PermissionNotFoundError),
)
async def get_permission(
    permission_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_authenticated_admin_user),
) -> Permission:
    return await repo.get_permission_or_404(db, permission_id)


@router.patch(
    "/{permission_id}",
    response_model=PermissionOut,
    responses=responses_from_api_errors(PermissionNotFoundError),
)
async def update_permission(
    permission_id: uuid.UUID,
    data: PermissionUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_authenticated_admin_user),
) -> Permission:
    perm = await repo.get_permission_or_404(db, permission_id)
    return await repo.update_permission(db, perm, data.action)


@router.delete(
    "/{permission_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=responses_from_api_errors(PermissionNotFoundError),
)
async def delete_permission(
    permission_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_authenticated_admin_user),
) -> Response:
    perm = await repo.get_permission_or_404(db, permission_id)
    await repo.delete_permission(db, perm)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
