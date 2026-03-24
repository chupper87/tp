import uuid
from datetime import date as date_type
from datetime import time as time_type

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from care_visits.errors import (
    CareVisitMustHaveEmployee,
    CareVisitNotFound,
    CustomerNotOnScheduleForVisit,
    EmployeeAlreadyOnVisit,
    EmployeeNotOnScheduleForVisit,
    EmployeeNotOnVisit,
    InvalidStatusTransition,
    MeasureAlreadyAssignedToVisit,
    OverlappingVisit,
)
from care_visits.schemas import (
    AddEmployeeToVisit,
    CareVisitCreate,
    CareVisitStatusUpdate,
    CareVisitUpdate,
)
from log_setup import get_logger
from models import (
    CareVisit,
    Employee,
    EmployeeCareVisit,
    ScheduleCustomer,
    ScheduleEmployee,
    ScheduleMeasure,
)

log = get_logger(__name__)

# Valid status transitions: current_status -> set of allowed next statuses
_VALID_TRANSITIONS: dict[str, set[str]] = {
    "planned": {
        "completed",
        "canceled",
        "no_show",
        "partially_completed",
        "rescheduled",
    },
    "partially_completed": {"completed"},
    "canceled": {"planned"},
    "no_show": {"planned"},
    "completed": set(),
    "rescheduled": set(),
}


def _relations() -> tuple:
    return (
        selectinload(CareVisit.employees).selectinload(EmployeeCareVisit.employee),
        selectinload(CareVisit.customer),
        selectinload(CareVisit.schedule_measures).selectinload(ScheduleMeasure.measure),
    )


async def get_care_visit_or_404(db: AsyncSession, care_visit_id: uuid.UUID) -> CareVisit:
    result = await db.execute(
        select(CareVisit)
        .where(CareVisit.id == care_visit_id)
        .options(*_relations())
        .execution_options(populate_existing=True)
    )
    care_visit = result.scalar_one_or_none()
    if care_visit is None:
        raise CareVisitNotFound(care_visit_id)
    return care_visit


async def list_care_visits(
    db: AsyncSession,
    *,
    schedule_id: uuid.UUID | None = None,
    customer_id: uuid.UUID | None = None,
    status: str | None = None,
    date_from: date_type | None = None,
    date_to: date_type | None = None,
) -> list[CareVisit]:
    q = select(CareVisit).options(*_relations())
    if schedule_id is not None:
        q = q.where(CareVisit.schedule_id == schedule_id)
    if customer_id is not None:
        q = q.where(CareVisit.customer_id == customer_id)
    if status is not None:
        q = q.where(CareVisit.status == status)
    if date_from is not None:
        q = q.where(CareVisit.date >= date_from)
    if date_to is not None:
        q = q.where(CareVisit.date <= date_to)
    result = await db.execute(q.order_by(CareVisit.date, CareVisit.created_at))
    return list(result.scalars().all())


async def list_care_visits_for_employee(
    db: AsyncSession,
    *,
    employee_id: uuid.UUID,
    status: str | None = None,
    date_from: date_type | None = None,
    date_to: date_type | None = None,
) -> list[CareVisit]:
    """List care visits where the given employee is assigned."""
    q = (
        select(CareVisit)
        .join(EmployeeCareVisit, EmployeeCareVisit.care_visit_id == CareVisit.id)
        .where(EmployeeCareVisit.employee_id == employee_id)
        .options(*_relations())
    )
    if status is not None:
        q = q.where(CareVisit.status == status)
    if date_from is not None:
        q = q.where(CareVisit.date >= date_from)
    if date_to is not None:
        q = q.where(CareVisit.date <= date_to)
    result = await db.execute(q.order_by(CareVisit.date, CareVisit.created_at))
    return list(result.scalars().all())


async def _check_employee_on_schedule(
    db: AsyncSession, schedule_id: uuid.UUID, employee_id: uuid.UUID
) -> None:
    """Verify employee is assigned to the schedule."""
    # Also verify employee exists
    emp = await db.execute(select(Employee).where(Employee.id == employee_id))
    if emp.scalar_one_or_none() is None:
        from employees.errors import EmployeeNotFound

        raise EmployeeNotFound(employee_id)

    result = await db.execute(
        select(ScheduleEmployee).where(
            ScheduleEmployee.schedule_id == schedule_id,
            ScheduleEmployee.employee_id == employee_id,
        )
    )
    if result.scalar_one_or_none() is None:
        raise EmployeeNotOnScheduleForVisit(employee_id, schedule_id)


async def _check_customer_on_schedule(
    db: AsyncSession, schedule_id: uuid.UUID, customer_id: uuid.UUID
) -> None:
    """Verify customer is assigned to the schedule."""
    result = await db.execute(
        select(ScheduleCustomer).where(
            ScheduleCustomer.schedule_id == schedule_id,
            ScheduleCustomer.customer_id == customer_id,
        )
    )
    if result.scalar_one_or_none() is None:
        raise CustomerNotOnScheduleForVisit(customer_id, schedule_id)


def _time_to_minutes(t: time_type) -> int:
    """Convert a time to minutes since midnight."""
    return t.hour * 60 + t.minute


async def _check_no_overlap(
    db: AsyncSession,
    schedule_id: uuid.UUID,
    employee_ids: list[uuid.UUID],
    start_time: time_type,
    duration: int,
    exclude_visit_id: uuid.UUID | None = None,
) -> None:
    """Check that no existing visit overlaps the given time window for any employee."""
    # Get all visits on this schedule that have a planned_start_time
    q = (
        select(CareVisit)
        .join(EmployeeCareVisit, EmployeeCareVisit.care_visit_id == CareVisit.id)
        .where(
            CareVisit.schedule_id == schedule_id,
            CareVisit.planned_start_time.isnot(None),
            EmployeeCareVisit.employee_id.in_(employee_ids),
        )
    )
    if exclude_visit_id is not None:
        q = q.where(CareVisit.id != exclude_visit_id)

    result = await db.execute(q.options(selectinload(CareVisit.employees)))
    existing_visits = list(result.scalars().unique().all())

    new_start = _time_to_minutes(start_time)
    new_end = new_start + duration

    for visit in existing_visits:
        if visit.planned_start_time is None:
            continue
        v_start = _time_to_minutes(visit.planned_start_time)
        v_end = v_start + visit.duration

        # Check overlap: two intervals [a, b) and [c, d) overlap if a < d and c < b
        if new_start < v_end and v_start < new_end:
            # Find which employee(s) overlap
            visit_emp_ids = {ecv.employee_id for ecv in visit.employees}
            for eid in employee_ids:
                if eid in visit_emp_ids:
                    raise OverlappingVisit(eid, visit.id)


async def _link_schedule_measures(
    db: AsyncSession,
    care_visit_id: uuid.UUID,
    schedule_measure_ids: list[uuid.UUID],
) -> int:
    """Link schedule measures to a care visit.

    Returns total duration of linked measures.
    """
    total_duration = 0
    for sm_id in schedule_measure_ids:
        result = await db.execute(
            select(ScheduleMeasure)
            .where(ScheduleMeasure.id == sm_id)
            .options(selectinload(ScheduleMeasure.measure))
        )
        sm = result.scalar_one_or_none()
        if sm is None:
            continue

        if sm.care_visit_id is not None and sm.care_visit_id != care_visit_id:
            raise MeasureAlreadyAssignedToVisit(sm_id, sm.care_visit_id)

        sm.care_visit_id = care_visit_id
        total_duration += sm.custom_duration or sm.measure.default_duration

    return total_duration


async def create_care_visit(db: AsyncSession, data: CareVisitCreate) -> CareVisit:
    # Validate customer is on the schedule
    await _check_customer_on_schedule(db, data.schedule_id, data.customer_id)

    # Validate all employees are on the schedule
    for emp in data.employees:
        await _check_employee_on_schedule(db, data.schedule_id, emp.employee_id)

    # Get the schedule to copy the date
    from models import Schedule

    sched_result = await db.execute(
        select(Schedule).where(Schedule.id == data.schedule_id)
    )
    schedule = sched_result.scalar_one()

    # If linking measures, compute duration from them when not explicitly provided
    duration = data.duration
    if data.schedule_measure_ids and duration is None:
        # Will be computed after linking measures
        duration = 0  # placeholder, will be updated below

    if duration is None:
        raise ValueError(
            "duration is required when schedule_measure_ids is not provided"
        )

    # Check for overlap if start time is provided
    employee_ids = [emp.employee_id for emp in data.employees]
    if data.planned_start_time is not None:
        await _check_no_overlap(
            db, data.schedule_id, employee_ids, data.planned_start_time, duration
        )

    care_visit = CareVisit(
        date=schedule.date,
        schedule_id=data.schedule_id,
        customer_id=data.customer_id,
        duration=duration,
        planned_start_time=data.planned_start_time,
        notes=data.notes,
        status="planned",
    )
    db.add(care_visit)
    await db.flush()

    for emp in data.employees:
        db.add(
            EmployeeCareVisit(
                care_visit_id=care_visit.id,
                employee_id=emp.employee_id,
                is_primary=emp.is_primary,
                notes=emp.notes,
            )
        )

    # Link schedule measures to this visit
    if data.schedule_measure_ids:
        measures_duration = await _link_schedule_measures(
            db, care_visit.id, data.schedule_measure_ids
        )
        # If duration was not explicitly provided, use sum of measure durations
        if data.duration is None and measures_duration > 0:
            care_visit.duration = measures_duration

    await db.commit()

    log.info(
        "created_care_visit",
        care_visit_id=str(care_visit.id),
        schedule_id=str(data.schedule_id),
        customer_id=str(data.customer_id),
        employee_count=len(data.employees),
    )
    return await get_care_visit_or_404(db, care_visit.id)


async def update_care_visit(
    db: AsyncSession, care_visit: CareVisit, data: CareVisitUpdate
) -> CareVisit:
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(care_visit, field, value)
    await db.commit()
    log.info("updated_care_visit", care_visit_id=str(care_visit.id))
    return await get_care_visit_or_404(db, care_visit.id)


async def update_status(
    db: AsyncSession, care_visit: CareVisit, data: CareVisitStatusUpdate
) -> CareVisit:
    current = care_visit.status
    requested = data.status
    allowed = _VALID_TRANSITIONS.get(current, set())
    if requested not in allowed:
        raise InvalidStatusTransition(current, requested)

    care_visit.status = requested
    await db.commit()
    log.info(
        "updated_care_visit_status",
        care_visit_id=str(care_visit.id),
        from_status=current,
        to_status=requested,
    )
    return await get_care_visit_or_404(db, care_visit.id)


async def delete_care_visit(db: AsyncSession, care_visit: CareVisit) -> None:
    await db.delete(care_visit)
    await db.commit()
    log.info("deleted_care_visit", care_visit_id=str(care_visit.id))


# --- Employee assignment (double bemanning) ---


async def add_employee(
    db: AsyncSession, care_visit: CareVisit, data: AddEmployeeToVisit
) -> CareVisit:
    # Employee must be on the schedule
    await _check_employee_on_schedule(db, care_visit.schedule_id, data.employee_id)

    # Check not already on visit
    existing = await db.execute(
        select(EmployeeCareVisit).where(
            EmployeeCareVisit.care_visit_id == care_visit.id,
            EmployeeCareVisit.employee_id == data.employee_id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise EmployeeAlreadyOnVisit(data.employee_id, care_visit.id)

    db.add(
        EmployeeCareVisit(
            care_visit_id=care_visit.id,
            employee_id=data.employee_id,
            is_primary=data.is_primary,
            notes=data.notes,
        )
    )
    await db.commit()
    log.info(
        "added_employee_to_visit",
        care_visit_id=str(care_visit.id),
        employee_id=str(data.employee_id),
    )
    return await get_care_visit_or_404(db, care_visit.id)


async def remove_employee(
    db: AsyncSession, care_visit: CareVisit, employee_id: uuid.UUID
) -> None:
    result = await db.execute(
        select(EmployeeCareVisit).where(
            EmployeeCareVisit.care_visit_id == care_visit.id,
            EmployeeCareVisit.employee_id == employee_id,
        )
    )
    ecv = result.scalar_one_or_none()
    if ecv is None:
        raise EmployeeNotOnVisit(employee_id, care_visit.id)

    # Don't allow removing the last employee
    count_result = await db.execute(
        select(EmployeeCareVisit).where(
            EmployeeCareVisit.care_visit_id == care_visit.id,
        )
    )
    if len(list(count_result.scalars().all())) <= 1:
        raise CareVisitMustHaveEmployee(care_visit.id)

    await db.delete(ecv)
    await db.commit()
    log.info(
        "removed_employee_from_visit",
        care_visit_id=str(care_visit.id),
        employee_id=str(employee_id),
    )
