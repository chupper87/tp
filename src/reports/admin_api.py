from datetime import date as date_type

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import get_authenticated_admin_user, get_db
from models import User
from reports import repo
from reports.schemas import (
    CustomerHoursReport,
    EmployeeHoursReport,
    VisitSummaryReport,
)

router = APIRouter(tags=["Reports (admin)"])


@router.get("/employee-hours", response_model=EmployeeHoursReport)
async def get_employee_hours(
    date_from: date_type,
    date_to: date_type,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_authenticated_admin_user),
) -> EmployeeHoursReport:
    return await repo.employee_hours(db, date_from, date_to)


@router.get("/customer-hours", response_model=CustomerHoursReport)
async def get_customer_hours(
    date_from: date_type,
    date_to: date_type,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_authenticated_admin_user),
) -> CustomerHoursReport:
    return await repo.customer_hours(db, date_from, date_to)


@router.get("/visit-summary", response_model=VisitSummaryReport)
async def get_visit_summary(
    date_from: date_type,
    date_to: date_type,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_authenticated_admin_user),
) -> VisitSummaryReport:
    return await repo.visit_summary(db, date_from, date_to)
