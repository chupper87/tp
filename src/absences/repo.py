import uuid
from datetime import date as date_type

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from absences.errors import AbsenceInvalidDateRange, AbsenceNotFound, AbsenceOverlap
from absences.schemas import AbsenceCreate, AbsenceUpdate
from employees.errors import EmployeeNotFound
from log_setup import get_logger
from models import Absence, Employee

log = get_logger(__name__)


def _relations() -> tuple:
    return (selectinload(Absence.employee),)


async def get_absence_or_404(db: AsyncSession, absence_id: uuid.UUID) -> Absence:
    result = await db.execute(
        select(Absence)
        .where(Absence.id == absence_id)
        .options(*_relations())
        .execution_options(populate_existing=True)
    )
    absence = result.scalar_one_or_none()
    if absence is None:
        raise AbsenceNotFound(absence_id)
    return absence


async def list_absences(
    db: AsyncSession,
    *,
    employee_id: uuid.UUID | None = None,
    absence_type: str | None = None,
    date_from: date_type | None = None,
    date_to: date_type | None = None,
) -> list[Absence]:
    q = select(Absence)
    if employee_id is not None:
        q = q.where(Absence.employee_id == employee_id)
    if absence_type is not None:
        q = q.where(Absence.absence_type == absence_type)
    if date_from is not None:
        q = q.where(Absence.end_date >= date_from)
    if date_to is not None:
        q = q.where(Absence.start_date <= date_to)
    result = await db.execute(q.order_by(Absence.start_date))
    return list(result.scalars().all())


async def _check_overlap(
    db: AsyncSession,
    employee_id: uuid.UUID,
    start_date: date_type,
    end_date: date_type,
    exclude_id: uuid.UUID | None = None,
) -> None:
    """Check for overlapping absences. Two ranges overlap when s1 <= e2 AND s2 <= e1."""
    q = select(Absence).where(
        and_(
            Absence.employee_id == employee_id,
            Absence.start_date <= end_date,
            Absence.end_date >= start_date,
        )
    )
    if exclude_id is not None:
        q = q.where(Absence.id != exclude_id)
    result = await db.execute(q)
    existing = result.scalar_one_or_none()
    if existing is not None:
        raise AbsenceOverlap(employee_id, start_date, end_date, existing.id)


async def create_absence(db: AsyncSession, data: AbsenceCreate) -> Absence:
    # Validate date range
    if data.start_date > data.end_date:
        raise AbsenceInvalidDateRange(data.start_date, data.end_date)

    # Validate employee exists
    emp = await db.execute(select(Employee).where(Employee.id == data.employee_id))
    if emp.scalar_one_or_none() is None:
        raise EmployeeNotFound(data.employee_id)

    # Check for overlaps
    await _check_overlap(db, data.employee_id, data.start_date, data.end_date)

    absence = Absence(
        employee_id=data.employee_id,
        absence_type=data.absence_type,
        start_date=data.start_date,
        end_date=data.end_date,
        hours=data.hours,
        notes=data.notes,
    )
    db.add(absence)
    await db.commit()
    log.info(
        "created_absence",
        absence_id=str(absence.id),
        employee_id=str(data.employee_id),
        type=data.absence_type,
    )
    return await get_absence_or_404(db, absence.id)


async def update_absence(
    db: AsyncSession, absence: Absence, data: AbsenceUpdate
) -> Absence:
    update_data = data.model_dump(exclude_unset=True)

    # Determine effective dates for overlap check
    new_start = update_data.get("start_date", absence.start_date)
    new_end = update_data.get("end_date", absence.end_date)

    if new_start > new_end:
        raise AbsenceInvalidDateRange(new_start, new_end)

    # Only check overlap if dates changed
    if "start_date" in update_data or "end_date" in update_data:
        await _check_overlap(
            db, absence.employee_id, new_start, new_end, exclude_id=absence.id
        )

    for field, value in update_data.items():
        setattr(absence, field, value)
    await db.commit()
    log.info("updated_absence", absence_id=str(absence.id))
    return await get_absence_or_404(db, absence.id)


async def delete_absence(db: AsyncSession, absence: Absence) -> None:
    await db.delete(absence)
    await db.commit()
    log.info("deleted_absence", absence_id=str(absence.id))
