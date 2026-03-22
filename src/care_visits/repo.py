import uuid
from datetime import date as date_type

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

    care_visit = CareVisit(
        date=schedule.date,
        schedule_id=data.schedule_id,
        customer_id=data.customer_id,
        duration=data.duration,
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
