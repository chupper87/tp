import uuid
from datetime import date as date_type
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from log_setup import get_logger
from models import AuditEntry

log = get_logger(__name__)


def _json_safe(obj: object) -> object:
    """Convert non-JSON-serializable types (date, datetime, UUID) to strings."""
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_json_safe(v) for v in obj]
    if isinstance(obj, (date_type, datetime)):
        return obj.isoformat()
    if isinstance(obj, uuid.UUID):
        return str(obj)
    return obj


async def audit_log(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    action: str,
    resource_type: str,
    resource_id: uuid.UUID,
    changes: dict | None = None,
) -> AuditEntry:
    """
    Record an audit entry for a mutation.

    Call this in repo functions after creates, updates, and deletes.
    The entry is written to the same transaction as the mutation
    (call before db.commit() or in a separate commit).
    """
    safe_changes = _json_safe(changes) if changes is not None else None
    entry = AuditEntry(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        changes=safe_changes,
    )
    db.add(entry)
    await db.commit()
    log.info(
        "audit_logged",
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id),
        user_id=str(user_id),
    )
    return entry


async def list_audit_entries(
    db: AsyncSession,
    *,
    resource_type: str | None = None,
    resource_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    date_from: date_type | None = None,
    date_to: date_type | None = None,
) -> list[AuditEntry]:
    q = select(AuditEntry)
    if resource_type is not None:
        q = q.where(AuditEntry.resource_type == resource_type)
    if resource_id is not None:
        q = q.where(AuditEntry.resource_id == resource_id)
    if user_id is not None:
        q = q.where(AuditEntry.user_id == user_id)
    if date_from is not None:
        q = q.where(AuditEntry.created_at >= date_from)
    if date_to is not None:
        from datetime import datetime, time, timezone

        end_of_day = datetime.combine(date_to, time.max, tzinfo=timezone.utc)
        q = q.where(AuditEntry.created_at <= end_of_day)
    result = await db.execute(q.order_by(AuditEntry.created_at.desc()))
    return list(result.scalars().all())
