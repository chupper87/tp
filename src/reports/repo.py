from datetime import date as date_type

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from log_setup import get_logger
from models import CareVisit, Employee, EmployeeCareVisit
from reports.schemas import (
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
