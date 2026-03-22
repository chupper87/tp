from datetime import date as date_type
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from care_visits import repo
from care_visits.schemas import CareVisitOut
from dependencies import get_current_employee, get_db
from models import CareVisit, Employee

router = APIRouter(prefix="/my", tags=["Care Visits (employee)"])


@router.get("/", response_model=list[CareVisitOut])
async def list_my_care_visits(
    status_filter: Optional[str] = None,
    date_from: Optional[date_type] = None,
    date_to: Optional[date_type] = None,
    db: AsyncSession = Depends(get_db),
    employee: Employee = Depends(get_current_employee),
) -> list[CareVisit]:
    return await repo.list_care_visits_for_employee(
        db,
        employee_id=employee.id,
        status=status_filter,
        date_from=date_from,
        date_to=date_to,
    )
