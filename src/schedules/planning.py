"""Planning intelligence: fulfillment, utilization, and continuity preview.

These are read-only query functions used by the schedule planning cockpit
to show admins coverage gaps, employee workload, and continuity impact.
"""

import uuid
from datetime import date as date_type, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models import (
    CustomerMeasure,
    Schedule,
    ScheduleCustomer,
    ScheduleEmployee,
    ScheduleMeasure,
)

# Standard shift durations in minutes
SHIFT_DURATIONS: dict[str, int] = {
    "morning": 480,  # 8h
    "day": 480,  # 8h
    "evening": 360,  # 6h
    "night": 600,  # 10h
}

LUNCH_DEDUCTION_MINUTES = 30
LUNCH_THRESHOLD_MINUTES = 360  # Deduct lunch for shifts >= 6h

# Map Python weekday (0=Monday) to day name
WEEKDAY_NAMES = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]


# ---------------------------------------------------------------------------
# Fulfillment
# ---------------------------------------------------------------------------


async def compute_fulfillment(db: AsyncSession, schedule: Schedule) -> dict:
    """Compute care plan fulfillment for each customer on the schedule.

    Returns a dict matching ScheduleFulfillmentOut schema.
    """
    # Get customers on this schedule
    result = await db.execute(
        select(ScheduleCustomer)
        .where(ScheduleCustomer.schedule_id == schedule.id)
        .options(selectinload(ScheduleCustomer.customer))
    )
    schedule_customers = list(result.scalars().all())

    if not schedule_customers:
        return {
            "schedule_id": schedule.id,
            "customers": [],
        }

    customer_ids = [sc.customer_id for sc in schedule_customers]

    # Get care plans for all customers in one query
    result = await db.execute(
        select(CustomerMeasure)
        .where(CustomerMeasure.customer_id.in_(customer_ids))
        .options(selectinload(CustomerMeasure.measure))
    )
    all_care_plans = list(result.scalars().all())

    # Get scheduled measures for this schedule
    result = await db.execute(
        select(ScheduleMeasure).where(ScheduleMeasure.schedule_id == schedule.id)
    )
    scheduled_measures = list(result.scalars().all())

    # Index scheduled measures by (customer_id, measure_id, time_of_day)
    scheduled_set: dict[tuple[uuid.UUID, uuid.UUID, str | None], ScheduleMeasure] = {}
    for sm in scheduled_measures:
        scheduled_set[(sm.customer_id, sm.measure_id, sm.time_of_day)] = sm

    # Group care plans by customer
    care_plans_by_customer: dict[uuid.UUID, list[CustomerMeasure]] = {}
    for cm in all_care_plans:
        care_plans_by_customer.setdefault(cm.customer_id, []).append(cm)

    # Determine the day of week for this schedule
    schedule_date: date_type = schedule.date
    day_name = WEEKDAY_NAMES[schedule_date.weekday()]

    customers_out = []
    for sc in schedule_customers:
        care_plans = care_plans_by_customer.get(sc.customer_id, [])
        required_measures = []
        total_required = 0
        total_fulfilled = 0
        total_duration = 0

        for cm in care_plans:
            # Determine if this measure is required on this day
            is_required = _is_required_on_day(cm, day_name)
            if is_required is None:
                continue  # Not applicable to this day

            key = (sc.customer_id, cm.measure_id, cm.time_of_day)
            sm = scheduled_set.get(key)
            is_fulfilled = sm is not None

            expected_duration = cm.customer_duration or cm.measure.default_duration

            if is_required:
                total_required += 1
                if is_fulfilled and sm is not None:
                    total_fulfilled += 1
                    total_duration += sm.custom_duration or expected_duration

            required_measures.append(
                {
                    "customer_measure_id": cm.id,
                    "measure_id": cm.measure_id,
                    "measure_name": cm.measure.name,
                    "frequency": cm.frequency,
                    "time_of_day": cm.time_of_day,
                    "expected_duration": expected_duration,
                    "is_required": is_required,
                    "is_fulfilled": is_fulfilled,
                    "schedule_measure_id": sm.id if sm else None,
                }
            )

        customers_out.append(
            {
                "customer_id": sc.customer_id,
                "customer_name": f"{sc.customer.first_name} {sc.customer.last_name}",
                "care_level": sc.customer.care_level,
                "required_measures": required_measures,
                "total_required": total_required,
                "total_fulfilled": total_fulfilled,
                "total_duration_minutes": total_duration,
            }
        )

    return {
        "schedule_id": schedule.id,
        "customers": customers_out,
    }


def _is_required_on_day(cm: CustomerMeasure, day_name: str) -> bool | None:
    """Determine if a customer measure should be done on a given day.

    Returns:
        True  = hard requirement (must be done)
        False = soft requirement (should be considered)
        None  = not applicable to this day
    """
    if cm.frequency == "daily":
        return True

    if cm.frequency == "weekly":
        if cm.days_of_week:
            if day_name in cm.days_of_week:
                return True
            return None  # Not required on this day
        # No specific days set — soft requirement
        return False

    # biweekly/monthly — soft requirement, shown as informational
    if cm.frequency in ("biweekly", "monthly"):
        return False

    return None


# ---------------------------------------------------------------------------
# Utilization
# ---------------------------------------------------------------------------


async def compute_utilization(db: AsyncSession, schedule: Schedule) -> dict:
    """Compute aggregate employee utilization for a schedule.

    Returns a dict matching ScheduleUtilizationOut schema.
    """
    # Count employees
    result = await db.execute(
        select(func.count())
        .select_from(ScheduleEmployee)
        .where(ScheduleEmployee.schedule_id == schedule.id)
    )
    employee_count = result.scalar() or 0

    # Sum planned durations from schedule measures
    result = await db.execute(
        select(ScheduleMeasure)
        .where(ScheduleMeasure.schedule_id == schedule.id)
        .options(selectinload(ScheduleMeasure.measure))
    )
    measures = list(result.scalars().all())

    total_planned = 0
    for sm in measures:
        total_planned += sm.custom_duration or sm.measure.default_duration

    # Compute capacity
    shift_type = schedule.shift_type
    base_capacity = SHIFT_DURATIONS.get(shift_type or "", 480)  # default 8h
    if base_capacity >= LUNCH_THRESHOLD_MINUTES:
        per_employee_capacity = base_capacity - LUNCH_DEDUCTION_MINUTES
    else:
        per_employee_capacity = base_capacity

    total_capacity = per_employee_capacity * max(employee_count, 1)
    utilization_pct = (total_planned / total_capacity * 100) if total_capacity > 0 else 0

    return {
        "schedule_id": schedule.id,
        "shift_type": shift_type,
        "total_planned_minutes": total_planned,
        "total_capacity_minutes": total_capacity,
        "employee_count": employee_count,
        "utilization_pct": round(utilization_pct, 1),
        "per_employee_avg_minutes": round(total_planned / max(employee_count, 1)),
        "per_employee_capacity_minutes": per_employee_capacity,
    }


# ---------------------------------------------------------------------------
# Continuity Preview
# ---------------------------------------------------------------------------


async def compute_continuity_preview(db: AsyncSession, schedule: Schedule) -> dict:
    """Compute continuity/familiarity for employee-customer pairs on a schedule.

    Looks at past 60 days of schedule co-assignments to determine how familiar
    each employee is with each customer.
    """
    # Get employees and customers on this schedule
    emp_result = await db.execute(
        select(ScheduleEmployee)
        .where(ScheduleEmployee.schedule_id == schedule.id)
        .options(selectinload(ScheduleEmployee.employee))
    )
    schedule_employees = list(emp_result.scalars().all())

    cust_result = await db.execute(
        select(ScheduleCustomer)
        .where(ScheduleCustomer.schedule_id == schedule.id)
        .options(selectinload(ScheduleCustomer.customer))
    )
    schedule_customers = list(cust_result.scalars().all())

    if not schedule_employees or not schedule_customers:
        return {
            "schedule_id": schedule.id,
            "average_familiarity": 0.0,
            "entries": [],
        }

    employee_ids = [se.employee_id for se in schedule_employees]
    customer_ids = [sc.customer_id for sc in schedule_customers]

    # Look back 60 days for schedule co-assignments
    cutoff = schedule.date - timedelta(days=60)

    # Find all schedules in the window that have any of these customers
    past_schedules_with_customers = (
        select(Schedule.id)
        .join(ScheduleCustomer, ScheduleCustomer.schedule_id == Schedule.id)
        .where(
            Schedule.date >= cutoff,
            Schedule.date < schedule.date,
            ScheduleCustomer.customer_id.in_(customer_ids),
        )
    ).subquery()

    # For those schedules, find which employees were also assigned
    result = await db.execute(
        select(
            ScheduleEmployee.employee_id,
            ScheduleCustomer.customer_id,
            func.count().label("shared_count"),
        )
        .select_from(ScheduleEmployee)
        .join(
            ScheduleCustomer,
            ScheduleCustomer.schedule_id == ScheduleEmployee.schedule_id,
        )
        .where(
            ScheduleEmployee.schedule_id.in_(select(past_schedules_with_customers.c.id)),
            ScheduleEmployee.employee_id.in_(employee_ids),
            ScheduleCustomer.customer_id.in_(customer_ids),
        )
        .group_by(ScheduleEmployee.employee_id, ScheduleCustomer.customer_id)
    )
    co_assignments = {
        (row.employee_id, row.customer_id): row.shared_count for row in result.all()
    }

    # Also get total schedule count per customer in the window
    result = await db.execute(
        select(
            ScheduleCustomer.customer_id,
            func.count(func.distinct(ScheduleCustomer.schedule_id)).label("total"),
        )
        .join(Schedule, Schedule.id == ScheduleCustomer.schedule_id)
        .where(
            Schedule.date >= cutoff,
            Schedule.date < schedule.date,
            ScheduleCustomer.customer_id.in_(customer_ids),
        )
        .group_by(ScheduleCustomer.customer_id)
    )
    customer_total_schedules = {row.customer_id: row.total for row in result.all()}

    # Build entries
    entries = []
    familiarity_scores = []

    emp_lookup = {se.employee_id: se.employee for se in schedule_employees}
    cust_lookup = {sc.customer_id: sc.customer for sc in schedule_customers}

    for eid in employee_ids:
        for cid in customer_ids:
            shared = co_assignments.get((eid, cid), 0)
            total = customer_total_schedules.get(cid, 0)
            score = shared / total if total > 0 else 0.0

            emp = emp_lookup[eid]
            cust = cust_lookup[cid]

            entries.append(
                {
                    "employee_id": eid,
                    "employee_name": f"{emp.first_name} {emp.last_name}",
                    "customer_id": cid,
                    "customer_name": f"{cust.first_name} {cust.last_name}",
                    "shared_schedules_last_60_days": shared,
                    "familiarity_score": round(score, 3),
                }
            )
            familiarity_scores.append(score)

    avg = (
        sum(familiarity_scores) / len(familiarity_scores) if familiarity_scores else 0.0
    )

    return {
        "schedule_id": schedule.id,
        "average_familiarity": round(avg, 3),
        "entries": entries,
    }
