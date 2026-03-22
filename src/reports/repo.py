from datetime import date as date_type

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from log_setup import get_logger
from models import CareVisit, Employee, EmployeeCareVisit
from reports.schemas import (
    ContinuityReport,
    ContinuityRow,
    CustomerHoursReport,
    CustomerHoursRow,
    EmployeeHoursReport,
    EmployeeHoursRow,
    VisitStatusCount,
    VisitSummaryReport,
)

log = get_logger(__name__)


async def employee_hours(
    db: AsyncSession,
    date_from: date_type,
    date_to: date_type,
) -> EmployeeHoursReport:
    """Sum of visit duration per employee for completed visits in date range.

    Each employee on a visit gets the full visit duration attributed to them,
    because in double bemanning both workers are present for the entire visit.
    """
    q = (
        select(
            EmployeeCareVisit.employee_id,
            Employee.first_name,
            Employee.last_name,
            func.coalesce(func.sum(CareVisit.duration), 0).label("total_minutes"),
            func.count(CareVisit.id).label("visit_count"),
        )
        .join(CareVisit, EmployeeCareVisit.care_visit_id == CareVisit.id)
        .join(Employee, EmployeeCareVisit.employee_id == Employee.id)
        .where(
            CareVisit.status == "completed",
            CareVisit.date >= date_from,
            CareVisit.date <= date_to,
        )
        .group_by(
            EmployeeCareVisit.employee_id,
            Employee.first_name,
            Employee.last_name,
        )
        .order_by(func.sum(CareVisit.duration).desc())
    )
    result = await db.execute(q)
    rows = [
        EmployeeHoursRow(
            employee_id=r.employee_id,
            first_name=r.first_name,
            last_name=r.last_name,
            total_minutes=r.total_minutes,
            visit_count=r.visit_count,
        )
        for r in result.all()
    ]
    return EmployeeHoursReport(date_from=date_from, date_to=date_to, rows=rows)


async def customer_hours(
    db: AsyncSession,
    date_from: date_type,
    date_to: date_type,
) -> CustomerHoursReport:
    """Sum of visit duration per customer for completed visits in date range."""
    from models import Customer

    q = (
        select(
            CareVisit.customer_id,
            Customer.first_name,
            Customer.last_name,
            func.coalesce(func.sum(CareVisit.duration), 0).label("total_minutes"),
            func.count(CareVisit.id).label("visit_count"),
        )
        .join(Customer, CareVisit.customer_id == Customer.id)
        .where(
            CareVisit.status == "completed",
            CareVisit.date >= date_from,
            CareVisit.date <= date_to,
        )
        .group_by(
            CareVisit.customer_id,
            Customer.first_name,
            Customer.last_name,
        )
        .order_by(func.sum(CareVisit.duration).desc())
    )
    result = await db.execute(q)
    rows = [
        CustomerHoursRow(
            customer_id=r.customer_id,
            first_name=r.first_name,
            last_name=r.last_name,
            total_minutes=r.total_minutes,
            visit_count=r.visit_count,
        )
        for r in result.all()
    ]
    return CustomerHoursReport(date_from=date_from, date_to=date_to, rows=rows)


async def visit_summary(
    db: AsyncSession,
    date_from: date_type,
    date_to: date_type,
) -> VisitSummaryReport:
    """Count of visits by status in date range."""
    q = (
        select(
            CareVisit.status,
            func.count(CareVisit.id).label("visit_count"),
        )
        .where(
            CareVisit.date >= date_from,
            CareVisit.date <= date_to,
        )
        .group_by(CareVisit.status)
        .order_by(CareVisit.status)
    )
    result = await db.execute(q)
    by_status = [
        VisitStatusCount(status=r.status, count=r.visit_count) for r in result.all()
    ]
    total = sum(s.count for s in by_status)
    return VisitSummaryReport(
        date_from=date_from, date_to=date_to, total=total, by_status=by_status
    )


async def customer_continuity(
    db: AsyncSession,
    date_from: date_type,
    date_to: date_type,
) -> ContinuityReport:
    """Continuity score per customer: how consistently they see the same workers.

    Formula: 1 - (unique_employees - 1) / (total_visits - 1)
    A score of 1.0 means perfect continuity (same worker every time).
    Double bemanning counts as 1 visit but adds both employees to the unique pool.
    """
    from models import Customer

    q = (
        select(
            CareVisit.customer_id,
            Customer.first_name,
            Customer.last_name,
            func.count(func.distinct(CareVisit.id)).label("total_visits"),
            func.count(func.distinct(EmployeeCareVisit.employee_id)).label(
                "unique_employees"
            ),
        )
        .join(EmployeeCareVisit, EmployeeCareVisit.care_visit_id == CareVisit.id)
        .join(Customer, CareVisit.customer_id == Customer.id)
        .where(
            CareVisit.status == "completed",
            CareVisit.date >= date_from,
            CareVisit.date <= date_to,
        )
        .group_by(
            CareVisit.customer_id,
            Customer.first_name,
            Customer.last_name,
        )
        .order_by(Customer.last_name, Customer.first_name)
    )
    result = await db.execute(q)
    rows = []
    for r in result.all():
        if r.total_visits <= 1:
            score = 1.0
        else:
            score = 1.0 - (r.unique_employees - 1) / (r.total_visits - 1)
        rows.append(
            ContinuityRow(
                customer_id=r.customer_id,
                first_name=r.first_name,
                last_name=r.last_name,
                total_visits=r.total_visits,
                unique_employees=r.unique_employees,
                continuity_score=round(score, 4),
            )
        )

    average_score = (
        round(sum(row.continuity_score for row in rows) / len(rows), 4) if rows else 0.0
    )

    return ContinuityReport(
        date_from=date_from,
        date_to=date_to,
        average_score=average_score,
        rows=rows,
    )
