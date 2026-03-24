import uuid
from datetime import date as date_type

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from customers.errors import CustomerNotFound
from employees.errors import EmployeeNotFound
from log_setup import get_logger
from measures.errors import MeasureNotFound
from models import (
    Absence,
    Customer,
    CustomerMeasure,
    Employee,
    Measure,
    Schedule,
    ScheduleCustomer,
    ScheduleEmployee,
    ScheduleMeasure,
)
from schedules.errors import (
    CustomerAlreadyOnSchedule,
    CustomerNotOnSchedule,
    CustomerNotOnScheduleForMeasure,
    EmployeeAbsenceConflict,
    EmployeeAlreadyOnSchedule,
    EmployeeNotOnSchedule,
    MeasureAlreadyOnSchedule,
    ScheduleConflict,
    ScheduleMeasureNotFound,
    ScheduleNotFound,
)
from schedules.schemas import (
    ScheduleCreate,
    ScheduleMeasureCreate,
    ScheduleMeasureUpdate,
    ScheduleUpdate,
)

log = get_logger(__name__)


def _relations() -> tuple:
    return (
        selectinload(Schedule.employees).selectinload(ScheduleEmployee.employee),
        selectinload(Schedule.customers).selectinload(ScheduleCustomer.customer),
        selectinload(Schedule.measures),
    )


async def get_schedule_or_404(db: AsyncSession, schedule_id: uuid.UUID) -> Schedule:
    result = await db.execute(
        select(Schedule)
        .where(Schedule.id == schedule_id)
        .options(*_relations())
        .execution_options(populate_existing=True)
    )
    schedule = result.scalar_one_or_none()
    if schedule is None:
        raise ScheduleNotFound(schedule_id)
    return schedule


async def list_schedules(
    db: AsyncSession,
    *,
    date_from: date_type | None = None,
    date_to: date_type | None = None,
    shift_type: str | None = None,
) -> list[Schedule]:
    q = select(Schedule)
    if date_from is not None:
        q = q.where(Schedule.date >= date_from)
    if date_to is not None:
        q = q.where(Schedule.date <= date_to)
    if shift_type is not None:
        q = q.where(Schedule.shift_type == shift_type)
    result = await db.execute(q.order_by(Schedule.date))
    return list(result.scalars().all())


async def list_schedules_for_employee(
    db: AsyncSession,
    *,
    employee_id: uuid.UUID,
    date_from: date_type | None = None,
    date_to: date_type | None = None,
    shift_type: str | None = None,
) -> list[Schedule]:
    """List schedules where the given employee is assigned."""
    q = (
        select(Schedule)
        .join(ScheduleEmployee, ScheduleEmployee.schedule_id == Schedule.id)
        .where(ScheduleEmployee.employee_id == employee_id)
    )
    if date_from is not None:
        q = q.where(Schedule.date >= date_from)
    if date_to is not None:
        q = q.where(Schedule.date <= date_to)
    if shift_type is not None:
        q = q.where(Schedule.shift_type == shift_type)
    result = await db.execute(q.order_by(Schedule.date))
    return list(result.scalars().all())


async def _get_by_date_and_shift(
    db: AsyncSession, d: date_type, shift_type: str
) -> Schedule | None:
    result = await db.execute(
        select(Schedule).where(Schedule.date == d, Schedule.shift_type == shift_type)
    )
    return result.scalar_one_or_none()


async def create_schedule(db: AsyncSession, data: ScheduleCreate) -> Schedule:
    if data.shift_type is not None:
        existing = await _get_by_date_and_shift(db, data.date, data.shift_type)
        if existing is not None:
            raise ScheduleConflict(str(data.date), data.shift_type)

    schedule = Schedule(
        date=data.date,
        shift_type=data.shift_type,
        custom_shift=data.custom_shift,
    )
    db.add(schedule)
    await db.commit()
    log.info("created_schedule", schedule_id=str(schedule.id), date=str(data.date))
    return await get_schedule_or_404(db, schedule.id)


async def update_schedule(
    db: AsyncSession, schedule: Schedule, data: ScheduleUpdate
) -> Schedule:
    update_data = data.model_dump(exclude_unset=True)

    if "shift_type" in update_data and update_data["shift_type"] is not None:
        new_date = update_data.get("date", schedule.date)
        new_shift = update_data["shift_type"]
        existing = await _get_by_date_and_shift(db, new_date, new_shift)
        if existing is not None and existing.id != schedule.id:
            raise ScheduleConflict(str(new_date), new_shift)

    for field, value in update_data.items():
        setattr(schedule, field, value)
    await db.commit()
    log.info("updated_schedule", schedule_id=str(schedule.id))
    return await get_schedule_or_404(db, schedule.id)


# --- Employee assignment ---


async def assign_employee(
    db: AsyncSession, schedule: Schedule, employee_id: uuid.UUID
) -> ScheduleEmployee:
    emp = await db.execute(select(Employee).where(Employee.id == employee_id))
    if emp.scalar_one_or_none() is None:
        raise EmployeeNotFound(employee_id)

    existing = await db.execute(
        select(ScheduleEmployee).where(
            ScheduleEmployee.schedule_id == schedule.id,
            ScheduleEmployee.employee_id == employee_id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise EmployeeAlreadyOnSchedule(employee_id, schedule.id)

    # Check for absences covering the schedule date
    absence_result = await db.execute(
        select(Absence).where(
            Absence.employee_id == employee_id,
            Absence.start_date <= schedule.date,
            Absence.end_date >= schedule.date,
        )
    )
    conflicting_absence = absence_result.scalar_one_or_none()
    if conflicting_absence is not None:
        raise EmployeeAbsenceConflict(employee_id, schedule.id, conflicting_absence.id)

    db.add(ScheduleEmployee(schedule_id=schedule.id, employee_id=employee_id))
    await db.commit()
    log.info(
        "assigned_employee_to_schedule",
        schedule_id=str(schedule.id),
        employee_id=str(employee_id),
    )

    result = await db.execute(
        select(ScheduleEmployee)
        .where(
            ScheduleEmployee.schedule_id == schedule.id,
            ScheduleEmployee.employee_id == employee_id,
        )
        .options(selectinload(ScheduleEmployee.employee))
    )
    return result.scalar_one()


async def remove_employee(
    db: AsyncSession, schedule: Schedule, employee_id: uuid.UUID
) -> None:
    result = await db.execute(
        select(ScheduleEmployee).where(
            ScheduleEmployee.schedule_id == schedule.id,
            ScheduleEmployee.employee_id == employee_id,
        )
    )
    se = result.scalar_one_or_none()
    if se is None:
        raise EmployeeNotOnSchedule(employee_id, schedule.id)
    await db.delete(se)
    await db.commit()
    log.info(
        "removed_employee_from_schedule",
        schedule_id=str(schedule.id),
        employee_id=str(employee_id),
    )


# --- Customer assignment ---


async def assign_customer(
    db: AsyncSession, schedule: Schedule, customer_id: uuid.UUID
) -> ScheduleCustomer:
    cust = await db.execute(select(Customer).where(Customer.id == customer_id))
    if cust.scalar_one_or_none() is None:
        raise CustomerNotFound(customer_id)

    existing = await db.execute(
        select(ScheduleCustomer).where(
            ScheduleCustomer.schedule_id == schedule.id,
            ScheduleCustomer.customer_id == customer_id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise CustomerAlreadyOnSchedule(customer_id, schedule.id)

    db.add(ScheduleCustomer(schedule_id=schedule.id, customer_id=customer_id))
    await db.commit()
    log.info(
        "assigned_customer_to_schedule",
        schedule_id=str(schedule.id),
        customer_id=str(customer_id),
    )

    result = await db.execute(
        select(ScheduleCustomer)
        .where(
            ScheduleCustomer.schedule_id == schedule.id,
            ScheduleCustomer.customer_id == customer_id,
        )
        .options(selectinload(ScheduleCustomer.customer))
    )
    return result.scalar_one()


async def remove_customer(
    db: AsyncSession, schedule: Schedule, customer_id: uuid.UUID
) -> None:
    result = await db.execute(
        select(ScheduleCustomer).where(
            ScheduleCustomer.schedule_id == schedule.id,
            ScheduleCustomer.customer_id == customer_id,
        )
    )
    sc = result.scalar_one_or_none()
    if sc is None:
        raise CustomerNotOnSchedule(customer_id, schedule.id)
    await db.delete(sc)
    await db.commit()
    log.info(
        "removed_customer_from_schedule",
        schedule_id=str(schedule.id),
        customer_id=str(customer_id),
    )


# --- Planned measures ---


async def get_schedule_measure_or_404(
    db: AsyncSession, schedule_measure_id: uuid.UUID
) -> ScheduleMeasure:
    result = await db.execute(
        select(ScheduleMeasure).where(ScheduleMeasure.id == schedule_measure_id)
    )
    sm = result.scalar_one_or_none()
    if sm is None:
        raise ScheduleMeasureNotFound(schedule_measure_id)
    return sm


async def add_measure(
    db: AsyncSession, schedule: Schedule, data: ScheduleMeasureCreate
) -> ScheduleMeasure:
    # Customer must be on this schedule
    on_schedule = await db.execute(
        select(ScheduleCustomer).where(
            ScheduleCustomer.schedule_id == schedule.id,
            ScheduleCustomer.customer_id == data.customer_id,
        )
    )
    if on_schedule.scalar_one_or_none() is None:
        raise CustomerNotOnScheduleForMeasure(data.customer_id, schedule.id)

    # Measure must exist
    measure = await db.execute(select(Measure).where(Measure.id == data.measure_id))
    if measure.scalar_one_or_none() is None:
        raise MeasureNotFound(data.measure_id)

    # Unique per (schedule, customer, measure)
    existing = await db.execute(
        select(ScheduleMeasure).where(
            ScheduleMeasure.schedule_id == schedule.id,
            ScheduleMeasure.customer_id == data.customer_id,
            ScheduleMeasure.measure_id == data.measure_id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise MeasureAlreadyOnSchedule(data.customer_id, data.measure_id)

    sm = ScheduleMeasure(
        schedule_id=schedule.id,
        customer_id=data.customer_id,
        measure_id=data.measure_id,
        time_of_day=data.time_of_day,
        custom_duration=data.custom_duration,
        notes=data.notes,
    )
    db.add(sm)
    await db.commit()
    log.info(
        "added_measure_to_schedule",
        schedule_id=str(schedule.id),
        customer_id=str(data.customer_id),
        measure_id=str(data.measure_id),
    )
    return await get_schedule_measure_or_404(db, sm.id)


async def update_measure(
    db: AsyncSession, sm: ScheduleMeasure, data: ScheduleMeasureUpdate
) -> ScheduleMeasure:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(sm, field, value)
    await db.commit()
    log.info("updated_schedule_measure", schedule_measure_id=str(sm.id))
    return await get_schedule_measure_or_404(db, sm.id)


async def remove_measure(db: AsyncSession, sm: ScheduleMeasure) -> None:
    await db.delete(sm)
    await db.commit()
    log.info("removed_schedule_measure", schedule_measure_id=str(sm.id))


# --- Auto-populate ---

WEEKDAY_NAMES = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]


async def auto_populate_measures(
    db: AsyncSession, schedule: Schedule, customer_id: uuid.UUID
) -> list[ScheduleMeasure]:
    """Auto-add applicable care plan measures for a customer on this schedule.

    Skips measures already on the schedule. Returns list of created ScheduleMeasures.
    """
    from sqlalchemy.orm import selectinload as sil

    # Verify customer is on schedule
    on_schedule = await db.execute(
        select(ScheduleCustomer).where(
            ScheduleCustomer.schedule_id == schedule.id,
            ScheduleCustomer.customer_id == customer_id,
        )
    )
    if on_schedule.scalar_one_or_none() is None:
        raise CustomerNotOnScheduleForMeasure(customer_id, schedule.id)

    # Get customer's care plan measures
    result = await db.execute(
        select(CustomerMeasure)
        .where(CustomerMeasure.customer_id == customer_id)
        .options(sil(CustomerMeasure.measure))
    )
    care_plans = list(result.scalars().all())

    # Get already-scheduled measures for this customer on this schedule
    result = await db.execute(
        select(ScheduleMeasure).where(
            ScheduleMeasure.schedule_id == schedule.id,
            ScheduleMeasure.customer_id == customer_id,
        )
    )
    existing_measure_ids = {sm.measure_id for sm in result.scalars().all()}

    # Determine day of week
    day_name = WEEKDAY_NAMES[schedule.date.weekday()]

    created: list[ScheduleMeasure] = []
    for cm in care_plans:
        # Skip if already on schedule
        if cm.measure_id in existing_measure_ids:
            continue

        # Check if applicable to this day
        if cm.frequency == "daily":
            pass  # Always applicable
        elif cm.frequency == "weekly":
            if cm.days_of_week and day_name not in cm.days_of_week:
                continue
        else:
            # biweekly/monthly — skip for auto-populate
            continue

        sm = ScheduleMeasure(
            schedule_id=schedule.id,
            customer_id=customer_id,
            measure_id=cm.measure_id,
            time_of_day=cm.time_of_day,
            custom_duration=cm.customer_duration,
        )
        db.add(sm)
        created.append(sm)

    if created:
        await db.commit()
        log.info(
            "auto_populated_measures",
            schedule_id=str(schedule.id),
            customer_id=str(customer_id),
            count=len(created),
        )

    return created
