from datetime import date as date_type
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import get_current_employee, get_db
from models import Employee, Schedule
from schedules import repo
from schedules.schemas import ScheduleOut

router = APIRouter(prefix="/my", tags=["Schedules (employee)"])


@router.get("/", response_model=list[ScheduleOut])
async def list_my_schedules(
    date_from: Optional[date_type] = None,
    date_to: Optional[date_type] = None,
    shift_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    employee: Employee = Depends(get_current_employee),
) -> list[Schedule]:
    return await repo.list_schedules_for_employee(
        db,
        employee_id=employee.id,
        date_from=date_from,
        date_to=date_to,
        shift_type=shift_type,
    )
