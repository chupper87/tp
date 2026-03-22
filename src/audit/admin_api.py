import uuid
from datetime import date as date_type
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from audit import repo
from audit.schemas import AuditEntryOut
from dependencies import get_authenticated_admin_user, get_db
from models import AuditEntry, User

router = APIRouter(tags=["Audit (admin)"])


@router.get("/", response_model=list[AuditEntryOut])
async def list_audit_entries(
    resource_type: Optional[str] = None,
    resource_id: Optional[uuid.UUID] = None,
    user_id: Optional[uuid.UUID] = None,
    date_from: Optional[date_type] = None,
    date_to: Optional[date_type] = None,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_authenticated_admin_user),
) -> list[AuditEntry]:
    return await repo.list_audit_entries(
        db,
        resource_type=resource_type,
        resource_id=resource_id,
        user_id=user_id,
        date_from=date_from,
        date_to=date_to,
    )
